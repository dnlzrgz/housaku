import asyncio
from typing import Any
from collections import Counter
import aiohttp
import feedparser
from sqlalchemy.orm import Session
from rich.status import Status
from housaku.utils import clean_html, tokenize, console
from housaku.repositories import DocRepository, PostingRepository, WordRepository
from housaku.models import Doc, Word, Posting


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


async def index_feeds(session: Session, status: Status, feeds: list[str]) -> None:
    doc_repo = DocRepository(session)
    posting_repo = PostingRepository(session)
    word_repo = WordRepository(session)

    async def process_feed(client: aiohttp.ClientSession, feed_url: str):
        try:
            entries = await fetch_feed(client, feed_url)
            for entry in entries:
                entry_link = entry.link
                uri = f"{entry_link}"

                doc_in_db = doc_repo.get_by_attributes(uri=uri)
                if doc_in_db:
                    console.print(f"[yellow][Skip][/] post already indexed: '{uri}'")
                    return

                content = await fetch_post(client, entry_link)
                result = tokenize(content)
                metadata = {
                    "title": entry.get("title", ""),
                    "link": entry_link,
                    "published": entry.get("published", ""),
                    "author": entry.get("author", ""),
                    "summary": entry.get("summary", ""),
                    "categories": [
                        category.term for category in entry.get("categories", [])
                    ],
                }

                doc_in_db = doc_repo.add(Doc(uri=uri, properties=metadata))
                tokens = Counter(result)

                for token, count in tokens.items():
                    word_in_db = word_repo.get_by_attributes(word=token)
                    if not word_in_db:
                        word_in_db = word_repo.add(Word(word=token))

                    posting_in_db = posting_repo.get_by_attributes(
                        word_id=word_in_db.id,
                        doc_id=doc_in_db.id,
                    )

                    if not posting_in_db:
                        posting_in_db = posting_repo.add(
                            Posting(
                                word=word_in_db,
                                doc=doc_in_db,
                                count=count,
                                tf=count / len(result),
                            )
                        )

                console.print(f"[green][Ok][/] indexed '{uri}'.")
                session.commit()
        except Exception as e:
            console.print(f"[red][Err][/] {e}")
            session.rollback()

    status.update(
        "[green]Indexing feeds and posts... Please wait, this may take a moment."
    )
    async with aiohttp.ClientSession() as client:
        tasks = [process_feed(client, feed) for feed in feeds]
        await asyncio.gather(*tasks)
