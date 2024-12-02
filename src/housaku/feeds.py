from typing import Any
from urllib.parse import urlparse
import asyncio
import aiohttp
import feedparser
from housaku.db import with_db
from housaku.utils import clean_html, console


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


async def index_feed(sqlite_url: str, feeds: list[str]) -> None:
    async def process_feed(client: aiohttp.ClientSession, feed_url: str):
        try:
            entries = await fetch_feed(client, feed_url)
            for entry in entries:
                with with_db(sqlite_url) as conn:
                    cursor = conn.cursor()
                    entry_link = entry.link
                    uri = f"{entry_link}"

                    cursor.execute(
                        "SELECT uri FROM documents WHERE uri = ?",
                        (uri,),
                    )
                    result = cursor.fetchone()

                    if result:
                        console.print(f'[yellow][Skip][/] already indexed "{uri}".')
                        return

                    body = await fetch_post(client, entry_link)
                    title = entry.get("title", entry_link)
                    protocol = urlparse(entry_link).scheme

                    cursor.execute(
                        """
                    INSERT INTO documents (uri, title, type, body)
                    VALUES (?, ?, ?, ?)
                    """,
                        (uri, title, protocol, body),
                    )
                    console.print(f'[green][Ok][/] indexed "{uri}".')
        except Exception as e:
            # TODO: Improve error message
            console.print(f"[red][Err][/] {e}")

    async with aiohttp.ClientSession() as client:
        tasks = [process_feed(client, feed) for feed in feeds]
        await asyncio.gather(*tasks)
