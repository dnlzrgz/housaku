from typing import Any
import aiohttp
import feedparser
from housaku.utils import clean_html


async def fetch_feed(client: aiohttp.ClientSession, feed_url: str) -> list[Any]:
    resp = await client.get(feed_url)
    if resp.status >= 400:
        raise Exception(f"something went wrong while fetching '{feed_url}'")

    content = await resp.text()
    d = feedparser.parse(content)
    if d.bozo:
        raise Exception(f"failed to parse '{feed_url}'")

    return [entry for entry in d.entries]


async def fetch_post(client: aiohttp.ClientSession, post_url: str) -> str:
    resp = await client.get(post_url)
    if resp.status >= 400:
        raise Exception(f"something went wrong while fetching '{post_url}'")

    html = await resp.text()
    cleaned_html = clean_html(html)
    return cleaned_html
