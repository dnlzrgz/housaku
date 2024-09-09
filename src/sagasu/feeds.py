import aiohttp
import feedparser

from sagasu.utils import clean_html


async def fetch_feed(client: aiohttp.ClientSession, feed_url: str) -> list[str]:
    resp = await client.get(feed_url)
    if resp.status >= 400:
        raise Exception(f"something went wrong while fetching '{feed_url}'")

    content = await resp.text()
    d = feedparser.parse(content)
    if d.bozo:
        raise Exception(f"failed to parse '{feed_url}'")

    return [entry.link for entry in d.entries]


async def fetch_post(client: aiohttp.ClientSession, post_url: str) -> str:
    resp = await client.get(post_url)
    if resp.status >= 400:
        raise Exception(f"something went wrong while fetching '{post_url}'")

    html = await resp.text()
    cleaned_html = clean_html(html)
    return cleaned_html


async def test():
    async with aiohttp.ClientSession() as client:
        links = await fetch_feed(client, "https://piccalil.li/feed.xml")
        for link in links:
            text = await fetch_post(client, link)
            print(text)
