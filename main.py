import asyncio
import json
import locale
import sys
from datetime import datetime, timedelta
from typing import List, Optional

import aiohttp
import pytz
import requests
import urllib3
import yaml
from loguru import logger
import xml.etree.ElementTree as ET
from email.utils import format_datetime
from pydantic import BaseModel, Field, HttpUrl, ValidationError

GENERATOR_VERSION = "0.3"
GENERATOR_NAME = f"smotrim.ru podcast generator v{GENERATOR_VERSION}"

OWNER_NAME = "Sergey"
OWNER_EMAIL = "me@coyotle.ru"
FUNDING_URL = "https://pay.cloudtips.ru/p/a368e9f8"

TIMEZONE = "Europe/Moscow"

ITUNES_NS = "http://www.itunes.com/dtds/podcast-1.0.dtd"
ATOM_NS = "http://www.w3.org/2005/Atom"
PODCAST_NS = "https://podcastindex.org/namespace/1.0"

ET.register_namespace("itunes", ITUNES_NS)
ET.register_namespace("atom", ATOM_NS)
ET.register_namespace("podcast", PODCAST_NS)

locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8")

logger.remove()
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss} | [<level>{level}</level>] | {message}",
    level="DEBUG",
    colorize=True,
)
logger.level("DEBUG", color="<cyan>")
logger.level("INFO", color="<green>")
logger.level("WARNING", color="<yellow>")
logger.level("ERROR", color="<red>")
logger.level("CRITICAL", color="<magenta>")

http = urllib3.PoolManager(
    headers={
        "Accept-Encoding": "identity",
    }
)


class PodcastModel(BaseModel):
    title: str
    description: str
    brand_id: Optional[int] = None
    rubric_id: Optional[int] = None
    station: str = Field(default="")
    category: str
    sub_category: Optional[str] = None
    website: HttpUrl
    feed: str
    image: HttpUrl


class StationModel(BaseModel):
    name: str
    id: int
    website: HttpUrl
    podcasts: List[PodcastModel]


class StationsDataModel(BaseModel):
    stations: List[StationModel]


class EpisodeModel(BaseModel):
    id: int
    brand_id: Optional[int] = None
    rubric_id: Optional[int] = None
    title: str
    anons: str = Field(default="")
    description: str = Field(default="")
    published: datetime
    duration: int
    media_url: str
    media_size: int
    picture_url: str


class XMLBuilder:
    """Helper for cleaner XML element creation"""
    
    @staticmethod
    def add_element(parent: Optional[ET.Element], tag: str, text_content: str = None, **attrs) -> ET.Element:
        """Add a simple text element. If parent is None, creates root element."""
        if parent is None:
            elem = ET.Element(tag, attrs)
        else:
            elem = ET.SubElement(parent, tag, attrs)
        if text_content:
            elem.text = text_content
        return elem
    
    @staticmethod
    def add_ns_element(parent: ET.Element, namespace: str, tag: str, text_content: str = None, **attrs) -> ET.Element:
        """Add a namespaced element"""
        full_tag = f"{{{namespace}}}{tag}"
        return XMLBuilder.add_element(parent, full_tag, text_content, **attrs)


class PodcastFeedGenerator:
    """Generates RSS podcast feeds"""
    
    def __init__(self, podcast: PodcastModel, episodes: List[EpisodeModel]):
        self.podcast = podcast
        self.episodes = episodes
        self.xml = XMLBuilder()
    
    def generate(self) -> str:
        """Generate complete RSS feed XML"""
        rss = self.xml.add_element(None, "rss", version="2.0")
        channel = self.xml.add_element(rss, "channel")
        
        self._add_channel_metadata(channel)
        self._add_channel_itunes_metadata(channel)
        self._add_episodes(channel)
        
        return ET.tostring(rss, encoding="utf-8", xml_declaration=True).decode("utf-8")
    
    def _add_channel_metadata(self, channel: ET.Element):
        """Add basic channel metadata"""
        self.xml.add_element(channel, "title", text_content=self.podcast.title)
        self.xml.add_element(channel, "link", text_content=str(self.podcast.website))
        self.xml.add_element(channel, "description", text_content=self.podcast.description)
        self.xml.add_element(channel, "language", text_content="ru-RU")
        self.xml.add_element(channel, "generator", text_content=GENERATOR_NAME)
        
        # Atom self-link
        self.xml.add_ns_element(
            channel, ATOM_NS, "link",
            href=self.podcast.feed,
            rel="self",
            type="application/rss+xml"
        )
        
        # Podcast namespace
        self.xml.add_ns_element(channel, PODCAST_NS, "locked", text_content="no")
    
    def _add_channel_itunes_metadata(self, channel: ET.Element):
        """Add iTunes-specific channel metadata"""
        self.xml.add_ns_element(channel, ITUNES_NS, "author", text_content=self.podcast.station)
        self.xml.add_ns_element(channel, ITUNES_NS, "explicit", text_content="false")
        
        # Owner
        owner = self.xml.add_ns_element(channel, ITUNES_NS, "owner")
        self.xml.add_ns_element(owner, ITUNES_NS, "name", text_content=OWNER_NAME)
        self.xml.add_ns_element(owner, ITUNES_NS, "email", text_content=OWNER_EMAIL)
        
        # Image
        self.xml.add_ns_element(channel, ITUNES_NS, "image", href=str(self.podcast.image))
        
        # Category - использует атрибут text, не текстовое содержимое
        category = self.xml.add_ns_element(channel, ITUNES_NS, "category", text=self.podcast.category)
        if self.podcast.sub_category:
            self.xml.add_ns_element(category, ITUNES_NS, "category", text=self.podcast.sub_category)
        
        # Funding
        if FUNDING_URL:
            self.xml.add_ns_element(
                channel, ITUNES_NS, "funding",
                text_content="Поддержите обновление подкаста",
                url=FUNDING_URL
            )
    
    def _add_episodes(self, channel: ET.Element):
        """Add episode items to channel"""
        for ep in self.episodes:
            item = self.xml.add_element(channel, "item")
            
            self.xml.add_element(item, "title", text_content=ep.anons)
            self.xml.add_element(item, "description", text_content=ep.description)
            self.xml.add_element(item, "guid", text_content=str(ep.id))
            self.xml.add_element(item, "pubDate", text_content=self._format_pub_date(ep))
            
            # Enclosure
            self.xml.add_element(
                item, "enclosure",
                url=ep.media_url,
                length=str(ep.media_size),
                type="audio/mpeg"
            )
            
            # iTunes episode metadata
            duration_str = str(timedelta(seconds=ep.duration))
            self.xml.add_ns_element(item, ITUNES_NS, "duration", text_content=duration_str)
            self.xml.add_ns_element(item, ITUNES_NS, "image", href=ep.picture_url)
    
    # TODO
    # Для эпизодов вышедших не в текущий день api возвращает дату без времени
    # Эпизоды одного подкаста вышедшие в один день могут сортироваться неправильно.
    def _format_pub_date(self, episode: EpisodeModel) -> str:
        """Format episode publication date"""
        pub_date = episode.published
        
        return format_datetime(pub_date.astimezone(pytz.timezone(TIMEZONE)))


def str_to_sec(time_str: str) -> int:
    time_parts = list(map(int, time_str.split(":")))
    seconds = sum(part * (60**i) for i, part in enumerate(reversed(time_parts)))
    return seconds


def parse_api_date(api_response: str) -> datetime:
    try:
        return datetime.strptime(api_response, "%d %B %Y")
    except ValueError:
        today = datetime.now(pytz.timezone(TIMEZONE)).date()
        time_object = datetime.strptime(api_response, "%H:%M").time()
        return pytz.timezone(TIMEZONE).localize(
            datetime.combine(today, time_object)
        )


async def get_media_size_async(session: aiohttp.ClientSession, url: str) -> int:
    """Асинхронно получает размер медиафайла через HEAD запрос"""
    try:
        async with session.head(url, allow_redirects=True, timeout=aiohttp.ClientTimeout(total=10)) as response:
            if response.status == 200:
                content_length = response.headers.get("Content-Length")
                if not content_length:
                    raise ValueError(f"No Content-Length header for {url}")
                return int(content_length)
            else:
                raise ValueError(f"HTTP {response.status} for {url}")
    except asyncio.TimeoutError:
        raise ValueError(f"Timeout getting media size for {url}")
    except aiohttp.ClientError as e:
        raise ValueError(f"Network error for {url}: {e}")


async def get_multiple_media_sizes(urls: List[str]) -> dict:
    async def safe_get_size(session: aiohttp.ClientSession, url: str) -> tuple:
        """обёртка возвращает (url, size) или (url, None)"""
        try:
            size = await get_media_size_async(session, url)
            return (url, size)
        except Exception as e:
            logger.error(f"Error getting media size: {e}")
            return (url, None)
    
    async with aiohttp.ClientSession() as session:
        tasks = [safe_get_size(session, url) for url in urls]
        results = await asyncio.gather(*tasks)
        return dict(results)


def fetch_raw_episodes(podcast: PodcastModel, limit=10):
    url = "https://smotrim.ru/api/audios"
    params = {
        "page": 1,
        "limit": limit,
    }

    if podcast.brand_id:
        params["brandId"] = podcast.brand_id
    elif podcast.rubric_id:
        params["rubricId"] = podcast.rubric_id

    r = http.request("GET", url, fields=params, preload_content=False, enforce_content_length=False, )

    try:
        data = r.read()
    except Exception as e:
        logger.error(f"Error reading response: {e}")
        if hasattr(e, 'partial'):
            data = e.partial
        else:
            return []
    finally:
        r.release_conn()

    try:
        payload = json.loads(data.decode("utf-8"))
    except json.JSONDecodeError:
        return []

    return payload["contents"][0]["list"]


def process_raw_episodes(
    raw_episodes: List[dict], podcast: PodcastModel
) -> List[EpisodeModel]:
    episodes = []
    
    # Собираем URL для параллельной обработки
    media_urls = []
    for raw_ep in raw_episodes:
        media_url = f"https://vgtrk-podcast.cdnvideo.ru/audio/listen?id={raw_ep['id']}"
        media_urls.append(media_url)
    
    # Получаем размеры параллельно
    logger.debug(f"Fetching sizes for {len(media_urls)} episodes...")
    try:
        media_sizes = asyncio.run(get_multiple_media_sizes(media_urls))
    except Exception as e:
        logger.error(f"Failed to fetch media sizes: {e}")
        return []
    logger.debug(f"Sizes fetched")
    
    # Обрабатываем эпизоды
    for raw_ep in raw_episodes:
        media_url = f"https://vgtrk-podcast.cdnvideo.ru/audio/listen?id={raw_ep['id']}"
        media_size = media_sizes.get(media_url)

        if not media_size or media_size <= 0:
            media_size = 0 
            logger.warning(f"Episode {raw_ep['id']} (media_url: {media_url}) - invalid or missing media size")

        try:
            resp = requests.get(raw_ep["player"]["preview"]["source"]["main"], timeout=10)
            resp.raise_for_status()
            picture_url = resp.url
        except Exception as e:
            logger.warning(f"Episode {raw_ep['id']} - failed to get picture URL: {e}")
            
        try:
            description = raw_ep["description"] or ""
            ep = EpisodeModel(
                id=raw_ep["id"],
                brand_id=podcast.brand_id,
                rubric_id=podcast.rubric_id,
                title=raw_ep["title"],
                published=parse_api_date(raw_ep["published"]),
                duration=str_to_sec(raw_ep["duration"]),
                anons=raw_ep["anons"],
                description=f"{description}",
                media_url=media_url,
                media_size=media_size,
                picture_url=picture_url,
            )
            episodes.append(ep)
        except Exception as e:
            logger.warning(f"Skipping episode {raw_ep['id']} - validation error: {e}")
            continue

    return episodes


def generate_podcast_feed_xml(
    podcast: PodcastModel, episodes: List[EpisodeModel]
) -> str:
    """Generate RSS XML feed for a podcast"""
    generator = PodcastFeedGenerator(podcast, episodes)
    return generator.generate()


def generate_podcast_feed(podcast: PodcastModel) -> str:
    if not (podcast.brand_id or podcast.rubric_id):
        raise ValueError("Neither brand_id nor rubric_id is provided")

    raw_episodes = fetch_raw_episodes(podcast)
    episodes = process_raw_episodes(raw_episodes, podcast)

    return generate_podcast_feed_xml(podcast, episodes)


def write_podcast_feed_to_file(podcast: PodcastModel, feed_str: str):
    filename = podcast.feed
    try:
        with open(filename, "w", encoding="utf-8") as file:
            file.write(feed_str)

        id = podcast.brand_id
        if podcast.rubric_id:
            id = podcast.rubric_id

        logger.info(f"-- {id:<6} {podcast.title:<24} \t {filename}")
    except Exception as e:
        logger.error(f"Error processing podcast {podcast.title}: {e}")


def create_station_feeds(station: StationModel):
    for podcast in station.podcasts:
        podcast.station = station.name
        try:
            feed_str = generate_podcast_feed(podcast)
            write_podcast_feed_to_file(podcast, feed_str)
        except Exception as e:
            logger.error(f'Can`t create feed for "{podcast.title}": {e}')


def main():
    try:
        with open("podcasts.yaml", "r") as file:
            yaml_data = yaml.safe_load(file)
            logger.info(f"Podcast list loaded from podcasts.yaml")
    except Exception as e:
        logger.error(f"Failed to load podcasts.yaml: {e}")
        sys.exit(1)

    try:
        stations_data = StationsDataModel(**yaml_data)
        logger.info(f"Data validation: OK")
    except ValidationError as e:
        logger.error(f"Data validation problem: {e}")
        sys.exit(1)

    for station in stations_data.stations:
        logger.info(f"- {station.name}")
        create_station_feeds(station)


if __name__ == "__main__":
    main()