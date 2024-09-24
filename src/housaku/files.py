from collections.abc import Generator
import os
import fnmatch
import mimetypes
from typing import Any, AsyncGenerator
from collections import deque, namedtuple
from datetime import datetime
from pathlib import Path
import frontmatter
from aiofile import async_open
import pymupdf
from housaku.utils import tokenize

Page = namedtuple("Page", ["uri", "tokens", "properties"])

other_filetypes = [
    "application/epub+zip",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
]


def list_files(root: Path, exclude: list[str] = []) -> Generator[Path, Any, Any]:
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
        return Page(file.resolve(), tokenize(content), metadata)


async def read_md(file: Path) -> Page:
    metadata = get_file_metadata(file)

    async with async_open(file, "r") as af:
        content = await af.read()
        post = frontmatter.loads(content)

        return Page(
            file.resolve(),
            tokenize(post.content),
            {**metadata, **{key: str(value) for key, value in post.metadata.items()}},
        )


async def read_pdf(file: Path) -> AsyncGenerator[Page, Any]:
    metadata = get_file_metadata(file)

    with pymupdf.open(file, filetype="pdf") as doc:
        for page in doc:
            yield Page(
                f"{file.resolve()}?page={page.number}",
                tokenize(page.get_text()),
                {
                    **metadata,
                    **doc.metadata,
                    "page": page.number,
                },
            )


async def read_generic_doc(file: Path) -> Page:
    metadata = get_file_metadata(file)

    tokens = []
    with pymupdf.open(file) as doc:
        for page in doc:
            tokens.extend(tokenize(page.get_text()))

        return Page(
            file.resolve(),
            tokens,
            {**metadata, **doc.metadata},
        )
