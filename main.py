import json
import locale
from datetime import datetime, timedelta
from typing import Optional

import pytz
import requests
import yaml
from loguru import logger
from pod2gen import Category, Episode, Funding, Media, Person, Podcast
from pydantic import BaseModel, Field


class PodcastItem(BaseModel):
    id: int
    brand_id: Optional[int] = None
    rubric_id: Optional[int] = None
    title: str
    description: str = Field(default="")
    published: datetime
    duration: int
    anons: str = Field(default="")
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
    try:
        response = requests.head(url, allow_redirects=True)
        return int(response.headers.get("Content-Length", 0))
    except requests.exceptions.RequestException as e:
        logger.error(f"Error getting media size: {e}")
        return 0


def create_podcast(podcast_info):
    p = Podcast()
    p.name = podcast_info["title"]
    p.description = podcast_info["description"]
    p.category = Category("News", "Politics")
    p.website = "https://smotrim.ru/radiovesti"
    p.authors = [Person("Вести ФМ")]
    p.owner = Person("Sergey", "me@coyotle.ru")
    p.explicit = False
    p.language = "ru-RU"
    p.image = podcast_info.get("image", "")
    funding = Funding(
        "Поддержите обновление подкаста", "https://pay.cloudtips.ru/p/a368e9f8"
    )
    p.add_funding(funding)
    p.generator = "RSS podcast generator v0.1"
    return p


def create_episode(podcast_item):
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


def get_podcast_episodes(podcast_id, is_rubric=False, limit=20):
    url = "https://smotrim.ru/api/audios"
    params = {
        "page": 1,
        "limit": limit,
        "rubricId" if is_rubric else "brandId": podcast_id,
    }

    r = requests.get(url, params=params)
    episodes = json.loads(r.text)["contents"][0]["list"]
    return [item for item in episodes if not item["isActive"]]


def process_podcast(podcast_info):
    brand_id = podcast_info.get("brand_id")
    rubric_id = podcast_info.get("rubric_id")

    if not (brand_id or rubric_id):
        raise ValueError("Neither brand_id nor rubric_id is provided in podcast_info")

    episodes = get_podcast_episodes(brand_id or rubric_id, is_rubric=bool(rubric_id))
    podcast = create_podcast(podcast_info)

    podcast = create_podcast(podcast_info)

    for item in episodes:
        media_url = f"https://vgtrk-podcast.cdnvideo.ru/audio/listen?id={item['id']}"
        media_size = get_media_size(media_url)

        if media_size <= 0:
            logger.warning(f"Skipping episode {item['id']} due to invalid media size")
            continue

        description = item["description"] or ""
        podcast_item = PodcastItem(
            id=item["id"],
            brand_id=podcast_info.get("brand_id", None),
            rubric_id=podcast_info.get("rubric_id", None),
            title=item["title"],
            published=parse_api_date(item["published"]),
            duration=str_to_sec(item["duration"]),
            anons=item["anons"],
            description=f"{description}\n\nПоддержите обновление подкаста:\nhttps://pay.cloudtips.ru/p/a368e9f8",
            media_url=media_url,
            media_size=media_size,
            picture_url=item["player"]["preview"]["source"]["main"],
        )

        episode = create_episode(podcast_item)
        podcast.episodes.append(episode)

    return podcast


def main():
    locale.setlocale(locale.LC_TIME, "ru_RU.UTF-8")

    try:
        with open("podcasts.yaml", "r") as file:
            podcasts = yaml.safe_load(file)
    except Exception as e:
        logger.error(f"Failed to load podcasts.yaml: {e}")
        return

    for podcast_info in podcasts:
        try:
            podcast = process_podcast(podcast_info)
            rss_feed = podcast.rss_str()

            filename = podcast_info["feed"]
            with open(filename, "w", encoding="utf-8") as file:
                file.write(rss_feed)
            logger.info(f"Generated RSS feed for {podcast_info['title']}: {filename}")
        except Exception as e:
            logger.error(f"Error processing podcast {podcast_info['title']}: {e}")
            continue

    logger.info("Finished processing all podcasts")


if __name__ == "__main__":
    main()
