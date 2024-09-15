import os
import fnmatch
import mimetypes
import warnings
from collections import deque, namedtuple
from datetime import datetime
from pathlib import Path
import frontmatter
from aiofile import async_open
import pymupdf
from housaku.utils import tokenize

DocInsights = namedtuple("DocInsights", ["tokens", "properties"])

other_filetypes = [
    "application/pdf",
    "application/epub+zip",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
]

# Supress ebooklib warnings.
warnings.filterwarnings("ignore", category=FutureWarning)


def list_files(root: Path, exclude: list[str] = []) -> list[Path]:
    if not root.is_dir():
        raise Exception(f"path '{root}' is not a directory")

    exclude_set = set(exclude)
    pending_dirs = deque([root])
    files = []

    while pending_dirs:
        dir = pending_dirs.popleft()
        for path in dir.iterdir():
            if any(fnmatch.fnmatch(path.name, pattern) for pattern in exclude_set):
                continue

            if path.is_dir():
                pending_dirs.append(path)

            if path.is_file():
                files.append(path.resolve())

    return files


async def extract_tokens(file: Path) -> DocInsights:
    mime_type, _ = mimetypes.guess_type(file)

    if mime_type == "text/plain":
        return await read_txt(file)
    if mime_type == "text/markdown":
        return await read_md(file)
    if mime_type in other_filetypes:
        return await read_generic_doc(file)
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


async def read_txt(file: Path) -> DocInsights:
    metadata = get_file_metadata(file)

    async with async_open(file, "r") as af:
        content = await af.read()
        return DocInsights(tokenize(content), metadata)


async def read_md(file: Path) -> DocInsights:
    metadata = get_file_metadata(file)

    async with async_open(file, "r") as af:
        content = await af.read()
        post = frontmatter.loads(content)

    return DocInsights(
        tokenize(post.content),
        {**metadata, **{key: str(value) for key, value in post.metadata.items()}},
    )


async def read_generic_doc(file: Path) -> DocInsights:
    metadata = get_file_metadata(file)

    tokens = []
    with pymupdf.open(file) as doc:
        for page in doc:
            tokens.extend(tokenize(page.get_text()))

    return DocInsights(tokens, {**metadata, **doc.metadata})
