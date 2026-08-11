import asyncio
import hashlib
import json
import locale
import os
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from email.utils import format_datetime
from typing import List, Optional

import aiohttp
import pytz
import requests
import urllib3
import yaml
from loguru import logger
from pydantic import BaseModel, Field, HttpUrl, ValidationError

GENERATOR_VERSION = "0.4a"
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
    brand_id: int
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
    brand_id: int
    title: str
    anons: str = Field(default="")
    description: str = Field(default="")
    published: datetime
    duration: int
    media_url: str
    media_size: int
    media_type: str = "audio/mpeg"
    picture_url: str


class XMLBuilder:
    """Helper for cleaner XML element creation"""

    @staticmethod
    def add_element(
        parent: Optional[ET.Element], tag: str, text_content: str = None, **attrs
    ) -> ET.Element:
        """Add a simple text element. If parent is None, creates root element."""
        if parent is None:
            elem = ET.Element(tag, attrs)
        else:
            elem = ET.SubElement(parent, tag, attrs)
        if text_content:
            elem.text = text_content
        return elem

    @staticmethod
    def add_ns_element(
        parent: ET.Element, namespace: str, tag: str, text_content: str = None, **attrs
    ) -> ET.Element:
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
        self.xml.add_element(
            channel, "description", text_content=self.podcast.description
        )
        self.xml.add_element(channel, "language", text_content="ru-RU")
        self.xml.add_element(channel, "generator", text_content=GENERATOR_NAME)

        # Atom self-link
        self.xml.add_ns_element(
            channel,
            ATOM_NS,
            "link",
            href=self.podcast.feed,
            rel="self",
            type="application/rss+xml",
        )

        # Podcast namespace
        self.xml.add_ns_element(channel, PODCAST_NS, "locked", text_content="no")

    def _add_channel_itunes_metadata(self, channel: ET.Element):
        """Add iTunes-specific channel metadata"""
        self.xml.add_ns_element(
            channel, ITUNES_NS, "author", text_content=self.podcast.station
        )
        self.xml.add_ns_element(channel, ITUNES_NS, "explicit", text_content="false")

        # Owner
        owner = self.xml.add_ns_element(channel, ITUNES_NS, "owner")
        self.xml.add_ns_element(owner, ITUNES_NS, "name", text_content=OWNER_NAME)
        self.xml.add_ns_element(owner, ITUNES_NS, "email", text_content=OWNER_EMAIL)

        # Image
        self.xml.add_ns_element(
            channel, ITUNES_NS, "image", href=str(self.podcast.image)
        )

        # Category - использует атрибут text, не текстовое содержимое
        category = self.xml.add_ns_element(
            channel, ITUNES_NS, "category", text=self.podcast.category
        )
        if self.podcast.sub_category:
            self.xml.add_ns_element(
                category, ITUNES_NS, "category", text=self.podcast.sub_category
            )

        # Funding
        if FUNDING_URL:
            self.xml.add_ns_element(
                channel,
                ITUNES_NS,
                "funding",
                text_content="Поддержите обновление подкаста",
                url=FUNDING_URL,
            )

    def _add_episodes(self, channel: ET.Element):
        """Add episode items to channel"""
        for ep in self.episodes:
            item = self.xml.add_element(channel, "item")

            self.xml.add_element(item, "title", text_content=ep.anons)
            self.xml.add_element(item, "description", text_content=ep.description)
            self.xml.add_element(item, "guid", text_content=str(ep.id))
            self.xml.add_element(
                item, "pubDate", text_content=self._format_pub_date(ep)
            )

            # Enclosure
            self.xml.add_element(
                item,
                "enclosure",
                url=ep.media_url,
                length=str(ep.media_size),
                type=ep.media_type,
            )

            # iTunes episode metadata
            duration_str = str(timedelta(seconds=ep.duration))
            self.xml.add_ns_element(
                item, ITUNES_NS, "duration", text_content=duration_str
            )
            self.xml.add_ns_element(item, ITUNES_NS, "image", href=ep.picture_url)

    # TODO
    # Для эпизодов вышедших не в текущий день api возвращает дату без времени
    # Эпизоды одного подкаста вышедшие в один день могут сортироваться неправильно.
    def _format_pub_date(self, episode: EpisodeModel) -> str:
        """Format episode publication date"""
        pub_date = episode.published

        return format_datetime(pub_date.astimezone(pytz.timezone(TIMEZONE)))


def parse_api_date(api_response: str) -> datetime:
    try:
        return datetime.strptime(api_response, "%d %B %Y")
    except ValueError:
        today = datetime.now(pytz.timezone(TIMEZONE)).date()
        time_object = datetime.strptime(api_response, "%H:%M").time()
        return pytz.timezone(TIMEZONE).localize(datetime.combine(today, time_object))


async def get_media_size_async(session: aiohttp.ClientSession, url: str) -> int:
    """Асинхронно получает размер медиафайла через HEAD запрос"""
    try:
        async with session.head(
            url, allow_redirects=True, timeout=aiohttp.ClientTimeout(total=5)
        ) as response:
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


EPISODE_FIELDS = """
id
title
number
season {
    number
}
status {
    enum
}
description
airDate
publicationDate
audio {
    duration
    publicId
}
fullVideo {
    ... on Video {
        publicId
        duration
    }
}
"""

# Объединённый запрос: за один HTTP-вызов тянет и список эпизодов подкаста
# (brand.podcastMaterials), и фильтр эпизодов (episodesFilter), и тип бренда.
# Для брендов типа Radiobroadcast работает episodesFilter,
# для нативных подкастов (тип Podcast) — podcastMaterials.
COMBINED_QUERY = """query CombinedEpisodes(
    $brandId: Int!
    $page: Int = 1
    $first: Int!
    $order: SortOrder = DESC
) {
    brand(id: $brandId) {
        type {
            enum
        }
        podcastMaterials(first: $first, page: $page) {
            data {
                ... on Episode {
__EPISODE_FIELDS__
                }
            }
        }
    }
    episodesFilter(
        brand_id: $brandId
        first: $first
        page: $page
        orderBy: { column: EPISODES_AIR_DATE, order: $order }
    ) {
        data {
            ... on Episode {
__EPISODE_FIELDS__
            }
        }
    }
}""".replace("__EPISODE_FIELDS__", EPISODE_FIELDS)


def graphql_request(operation_name: str, query: str, variables: dict) -> dict:
    """Send a GraphQL request to smotrim.ru API"""
    body_dict = {
        "operationName": operation_name,
        "variables": variables,
        "query": query,
    }

    body_str = json.dumps(body_dict, separators=(",", ":"), ensure_ascii=False)
    body_hash = hashlib.md5(body_str.encode()).hexdigest()

    vars_str = json.dumps(variables, separators=(",", ":"))
    vars_hash = hashlib.md5(vars_str.encode()).hexdigest()

    url = (
        f"https://apis.smotrim.ru/graphql?page={operation_name}"
        f"&body={body_hash}&vars={vars_hash}"
    )

    response = requests.post(
        url,
        data=body_str,
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0",
            "Origin": "https://smotrim.ru",
            "Referer": "https://smotrim.ru/",
        },
        timeout=10,
    )

    return response.json()


def filter_episodes_with_stream(episodes: list) -> list:
    """Оставляем эпизоды с airDate и хотя бы одним источником (аудио или видео)"""
    return [
        e
        for e in episodes
        if e.get("airDate") is not None
        and (e.get("audio") or (e.get("fullVideo") or {}).get("publicId"))
    ]


def enrich_with_mp3(episodes: list):
    """Дополняет каждый эпизод mp3 ссылкой через player-api"""
    for ep in episodes:
        audio = ep.get("audio")
        if not audio or not audio.get("publicId"):
            continue

        audio_id = audio["publicId"]
        try:
            r = requests.get(
                f"https://player-api.smotrim.ru/api/v1/audio/{audio_id}",
                timeout=10,
            )
            r.raise_for_status()
            audio_data = r.json().get("data", {})
            audio["mp3"] = audio_data.get("streams", {}).get("mp3")
        except Exception as ex:
            logger.warning(
                f"Failed to get audio URL for episode {ep.get('id')}: {ex}"
            )


def enrich_video_with_m3u8(episodes: list):
    """Дополняет видео-эпизоды ссылкой на HLS-плейлист через player-api"""
    for ep in episodes:
        if ep.get("audio"):
            continue
        video = ep.get("fullVideo") or {}
        if not video.get("publicId"):
            continue

        video_id = video["publicId"]
        try:
            r = requests.get(
                f"https://player-api.smotrim.ru/api/v1/video/{video_id}",
                timeout=10,
            )
            r.raise_for_status()
            video_data = r.json().get("data", {})
            video["m3u8"] = video_data.get("streams", {}).get("m3u8")
        except Exception as ex:
            logger.warning(
                f"Failed to get video URL for episode {ep.get('id')}: {ex}"
            )


def fetch_raw_episodes(podcast: PodcastModel, limit=20):
    variables = {
        "brandId": podcast.brand_id,
        "page": 1,
        "first": limit,
        "order": "DESC",
    }

    data = graphql_request("CombinedEpisodes", COMBINED_QUERY, variables)

    if "data" not in data:
        logger.error(f"Invalid GraphQL response structure for {podcast.title}")
        return []

    payload = data["data"]
    brand = payload.get("brand") or {}
    brand_type = (brand.get("type") or {}).get("enum")
    podcast_materials = (brand.get("podcastMaterials") or {}).get("data") or []

    if podcast_materials:
        logger.debug(
            f"{podcast.title}: brand type {brand_type}, using podcastMaterials"
        )
        return filter_episodes_with_stream(podcast_materials)

    episodes_filter = (payload.get("episodesFilter") or {}).get("data") or []
    logger.debug(
        f"{podcast.title}: brand type {brand_type}, using episodesFilter"
    )
    return filter_episodes_with_stream(episodes_filter)


def process_raw_episodes(
    raw_episodes: List[dict], podcast: PodcastModel
) -> List[EpisodeModel]:
    episodes = []

    enrich_with_mp3(raw_episodes)
    enrich_video_with_m3u8(raw_episodes)

    audio_episodes = [e for e in raw_episodes if (e.get("audio") or {}).get("mp3")]
    video_episodes = [
        e
        for e in raw_episodes
        if not (e.get("audio") or {}).get("mp3")
        and (e.get("fullVideo") or {}).get("m3u8")
    ]

    if not audio_episodes and not video_episodes:
        logger.warning(f"No episodes with media stream for {podcast.title}")
        return []

    # Получаем размеры mp3 параллельно
    media_urls = [e["audio"]["mp3"] for e in audio_episodes]
    media_sizes = {}
    if media_urls:
        logger.debug(f"Fetching sizes for {len(media_urls)} episodes...")
        try:
            media_sizes = asyncio.run(get_multiple_media_sizes(media_urls))
        except Exception as e:
            logger.error(f"Failed to fetch media sizes: {e}")
            return []
        logger.debug(f"Sizes fetched")

    def build_episode(raw_ep, media_url, media_size, media_type, duration):
        description = raw_ep["description"] or ""
        return EpisodeModel(
            id=raw_ep["id"],
            brand_id=podcast.brand_id,
            title=raw_ep["title"],
            published=datetime.strptime(raw_ep["airDate"], "%Y-%m-%dT%H:%M:%S%z"),
            duration=duration,
            anons=raw_ep["title"],
            description=f"{description}",
            media_url=media_url,
            media_size=media_size,
            media_type=media_type,
            picture_url=str(podcast.image),
        )

    for raw_ep in audio_episodes:
        media_url = raw_ep["audio"]["mp3"]
        media_size = media_sizes.get(media_url)

        if not media_size or media_size <= 0:
            media_size = 0
            logger.warning(
                f"Episode {raw_ep['id']} (media_url: {media_url}) - invalid or missing media size"
            )

        try:
            episodes.append(
                build_episode(
                    raw_ep,
                    media_url,
                    media_size,
                    "audio/mpeg",
                    raw_ep["audio"]["duration"],
                )
            )
        except Exception as e:
            logger.warning(f"Skipping episode {raw_ep['id']} - validation error: {e}")
            continue

    for raw_ep in video_episodes:
        duration = (raw_ep.get("fullVideo") or {}).get("duration")
        try:
            episodes.append(
                build_episode(
                    raw_ep,
                    raw_ep["fullVideo"]["m3u8"],
                    0,
                    "application/vnd.apple.mpegurl",
                    round(duration) if duration else 0,
                )
            )
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
    if not podcast.brand_id:
        raise ValueError("brand_id is not provided")

    raw_episodes = fetch_raw_episodes(podcast)
    if len(raw_episodes) == 0:
        logger.warning("Episodes list is empty")

    episodes = process_raw_episodes(raw_episodes, podcast)

    return generate_podcast_feed_xml(podcast, episodes)


def write_podcast_feed_to_file(podcast: PodcastModel, feed_str: str):
    filename = podcast.feed
    try:
        # Не затираем существующий feed, если новых эпизодов нет
        if feed_str.count("<item>") == 0 and os.path.exists(filename):
            logger.warning(
                f"Skip empty feed for {podcast.title}, keeping existing {filename}"
            )
            return

        with open(filename, "w", encoding="utf-8") as file:
            file.write(feed_str)

        logger.info(f"-- {podcast.brand_id:<6} {podcast.title:<24} \t {filename}")
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


def write_opml(stations_data: StationsDataModel):
    """Генерирует podcasts.opml.xml из списка подкастов"""
    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8" standalone="no" ?>')
    lines.append('<opml version="2.0">')
    lines.append('\t<head>')
    lines.append('\t\t<title>Подкасты платформы Смотрим</title>')
    lines.append(
        '\t\t<dateCreated>'
        + datetime.now().strftime("%d %b %y %H:%M:%S +0000")
        + "</dateCreated>"
    )
    lines.append("\t</head>")
    lines.append("\t<body>")
    for station in stations_data.stations:
        lines.append(f'\t\t<outline text="{station.name}">')
        for podcast in station.podcasts:
            xml_url = "https://rss.coyotle.ru/" + podcast.feed.replace("docs/", "")
            lines.append(
                f'\t\t\t<outline text="{podcast.title}" type="rss" '
                f'xmlUrl="{xml_url}" htmlUrl="{podcast.website}"/>'
            )
        lines.append("\t\t</outline>")
    lines.append("\t</body>")
    lines.append("</opml>")

    with open("docs/podcasts.opml.xml", "w", encoding="utf-8") as file:
        file.write("\n".join(lines) + "\n")

    logger.info("OPML file updated: docs/podcasts.opml.xml")


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

    write_opml(stations_data)


if __name__ == "__main__":
    main()
