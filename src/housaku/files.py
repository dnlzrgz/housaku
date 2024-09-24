import os
import asyncio
import fnmatch
import mimetypes
from collections.abc import Generator
from concurrent.futures import ThreadPoolExecutor
from typing import Any, AsyncGenerator
from collections import deque
from datetime import datetime
from pathlib import Path
import frontmatter
from aiofile import async_open
import pymupdf
from housaku.utils import tokenize


class Page:
    def __init__(
        self,
        parent_uri: str | None,
        uri: str,
        tokens: list[str],
        properties: dict,
    ) -> None:
        self.parent_uri = parent_uri
        self.uri = uri
        self.tokens = tokens
        self.properties = properties


other_filetypes = [
    "application/epub+zip",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
]


def list_files(root: Path, exclude: list[str] = []) -> Generator[Path, None, None]:
    if not root.is_dir():
        raise Exception(f"path '{root}' is not a directory")

    exclude_set = set(exclude)
    pending_dirs = deque([root])

    while pending_dirs:
        dir = pending_dirs.popleft()
        for path in dir.iterdir():
            if any(fnmatch.fnmatch(path.name, pattern) for pattern in exclude_set):
                continue

            if path.is_dir():
                pending_dirs.append(path)

            if path.is_file():
                yield path.resolve()


async def extract_tokens(file: Path) -> AsyncGenerator[Page, Any]:
    mime_type, _ = mimetypes.guess_type(file)

    if mime_type == "text/plain":
        yield await read_txt(file)
    if mime_type == "text/markdown":
        yield await read_md(file)
    if mime_type == "application/pdf":
        async for page in read_pdf(file):
            yield page
    if mime_type in other_filetypes:
        yield await read_generic_doc(file)
    else:
        raise Exception(f"Unsupported file format {mime_type}")


def get_file_metadata(file: Path) -> dict:
    file_stats = os.stat(file)
    return {
        "name": file.name,
        "size": file_stats.st_size,
        "created_at": datetime.fromtimestamp(file_stats.st_ctime).isoformat(),
        "last_modified": datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
    }


async def read_txt(file: Path) -> Page:
    metadata = get_file_metadata(file)

    async with async_open(file, "r") as af:
        content = await af.read()
        return Page(
            None,
            f"{file.resolve()}",
            tokenize(content),
            metadata,
        )


async def read_md(file: Path) -> Page:
    metadata = get_file_metadata(file)

    async with async_open(file, "r") as af:
        content = await af.read()
        post = frontmatter.loads(content)

        return Page(
            None,
            f"{file.resolve()}",
            tokenize(post.content),
            metadata | {key: f"{value}" for key, value in post.metadata.items()},
        )


def _read_pdf(file: Path) -> list[Page]:
    metadata = get_file_metadata(file)
    uri = f"{file.resolve()}"

    with pymupdf.open(file, filetype="pdf") as doc:
        pages = [Page(None, uri, [], metadata | doc.metadata)]

        for page in doc:
            pages.append(
                Page(
                    uri,
                    f"{uri}?page={page.number}",
                    tokenize(page.get_text()),
                    {"page": page.number},
                )
            )

        return pages


async def read_pdf(file: Path) -> AsyncGenerator[Page, Any]:
    loop = asyncio.get_running_loop()

    with ThreadPoolExecutor() as pool:
        for page in await loop.run_in_executor(pool, _read_pdf, file):
            yield page


def _read_generic_doc(file: Path) -> Page:
    metadata = get_file_metadata(file)

    tokens = []
    with pymupdf.open(file) as doc:
        for page in doc:
            tokens.extend(tokenize(page.get_text()))

        return Page(
            None,
            f"{file.resolve()}",
            tokens,
            metadata | doc.metadata,
        )


async def read_generic_doc(file: Path) -> Page:
    loop = asyncio.get_running_loop()

    with ThreadPoolExecutor() as pool:
        result = await loop.run_in_executor(pool, _read_generic_doc, file)
        return result
