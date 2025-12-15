import json
import locale
import sys
from datetime import datetime, timedelta
from typing import List, Optional

import pytz
import requests
import urllib3
import yaml
from loguru import logger
from pod2gen import Category, Episode, Funding, Media, Person, Podcast
from pydantic import BaseModel, Field, HttpUrl, ValidationError

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


def str_to_sec(time_str: str) -> int:
    time_parts = list(map(int, time_str.split(":")))
    seconds = sum(part * (60**i) for i, part in enumerate(reversed(time_parts)))
    return seconds


def parse_api_date(api_response: str) -> datetime:
    try:
        return datetime.strptime(api_response, "%d %B %Y")
    except ValueError:
        today = datetime.now(pytz.timezone("Europe/Moscow")).date()
        time_object = datetime.strptime(api_response, "%H:%M").time()
        return pytz.timezone("Europe/Moscow").localize(
            datetime.combine(today, time_object)
        )


def get_media_size(url: str) -> int:
    response = requests.head(url, allow_redirects=True)
    if response.status_code == 200:
        return int(response.headers.get("Content-Length", 0))
    else:
        logger.error(
            f"Error getting media size: HTTP status code {response.status_code}"
        )
        return 0


def build_p2g_podcast(podcast: PodcastModel):
    pcast = Podcast()
    pcast.name = podcast.title
    pcast.description = podcast.description
    pcast.category = Category(podcast.category, podcast.sub_category)
    pcast.website = str(podcast.website)
    pcast.authors = [Person(podcast.station)]
    pcast.owner = Person("Sergey", "me@coyotle.ru")
    pcast.explicit = False
    pcast.language = "ru-RU"
    pcast.image = str(podcast.image)

    funding = Funding(
        "Поддержите обновление подкаста", "https://pay.cloudtips.ru/p/a368e9f8"
    )
    pcast.add_funding(funding)
    pcast.generator = "Smotrim podcast generator v0.2"
    return pcast


def build_p2g_episode(podcast_item):
    ep = Episode()
    ep.title = podcast_item.anons
    ep.long_summary = podcast_item.description

    published = podcast_item.published
    if published.time() == datetime.min.time():
        published += timedelta(seconds=podcast_item.id % 1000)

    ep.publication_date = published.astimezone(pytz.timezone("Europe/Moscow"))
    ep.image = podcast_item.picture_url

    ep.media = Media(
        podcast_item.media_url,
        type="audio/mpeg",
        duration=timedelta(seconds=podcast_item.duration),
        size=podcast_item.media_size,
    )
    return ep


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

    r = http.request(
        "GET",
        url,
        fields=params,
        preload_content=False,
        enforce_content_length=False,  # ignore content-lenght errors
    )

    try:
        data = r.read()  # читает всё, что реально пришло
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
    for raw_ep in raw_episodes:
        media_url = f"https://vgtrk-podcast.cdnvideo.ru/audio/listen?id={raw_ep['id']}"
        media_size = get_media_size(media_url)

        if media_size <= 0:
            logger.warning(f"Skipping episode {raw_ep['id']} due to invalid media size")
            continue

        resp = requests.get(raw_ep["player"]["preview"]["source"]["main"])
        picture_url = resp.url

        description = raw_ep["description"] or ""
        ep = EpisodeModel(
            id=raw_ep["id"],
            brand_id=podcast.brand_id,
            rubric_id=podcast.rubric_id,
            title=raw_ep["title"],
            published=parse_api_date(raw_ep["published"]),
            duration=str_to_sec(raw_ep["duration"]),
            anons=raw_ep["anons"],
            description=f"{description}\n\nПоддержите обновление подкаста:\nhttps://pay.cloudtips.ru/p/a368e9f8",
            media_url=media_url,
            media_size=media_size,
            picture_url=picture_url,
        )
        episodes.append(ep)

    return episodes


def generate_podcast_feed(podcast: PodcastModel) -> Podcast:
    if not (podcast.brand_id or podcast.rubric_id):
        raise ValueError("Neither brand_id nor rubric_id is provided in podcast_info")

    raw_episodes = fetch_raw_episodes(podcast)
    episodes = process_raw_episodes(raw_episodes, podcast)

    p2g_podcast = build_p2g_podcast(podcast)
    for ep in episodes:
        p2g_episode = build_p2g_episode(ep)
        p2g_podcast.episodes.append(p2g_episode)

    return p2g_podcast


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
            podcast_feed = generate_podcast_feed(podcast)
            feed_str = podcast_feed.rss_str()
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
