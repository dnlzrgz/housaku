from pathlib import Path
from typing import Any, Generator
import fnmatch
import mimetypes
import warnings
from aiofile import async_open
from ebooklib import epub
from pypdf import PdfReader
from docx import Document
import ebooklib
import frontmatter
from sagasu.utils import tokenize

# Supress ebooklib warnings.
warnings.filterwarnings("ignore", category=FutureWarning)


def list_files(root: Path, exclude: list[str] = []) -> Generator[Path, Any, Any]:
    if not root.is_dir():
        raise Exception(f"path '{root}' is not a directory")

    exclude_set = set(exclude)
    pending_dirs = [root]
    while pending_dirs:
        dir = pending_dirs.pop()
        for path in dir.iterdir():
            if any(fnmatch.fnmatch(path.name, pattern) for pattern in exclude_set):
                continue

            if path.is_dir():
                pending_dirs.append(path)

            if path.is_file():
                yield path.resolve()


async def extract_tokens(file: Path) -> list[str]:
    mime_type, _ = mimetypes.guess_type(file)

    if mime_type == "text/plain":
        return await read_txt(file)
    if mime_type == "text/markdown":
        return await read_md(file)
    if mime_type == "application/pdf":
        return await read_pdf(file)
    if mime_type == "application/epub+zip":
        return await read_epub(file)
    if (
        mime_type
        == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    ):
        return await read_docx(file)
    else:
        raise Exception(f"Unsupported file format {mime_type}")


async def read_txt(file: Path) -> list[str]:
    async with async_open(file, "r") as af:
        content = await af.read()
        return tokenize(content)


async def read_md(file: Path) -> list[str]:
    async with async_open(file, "r") as af:
        content = await af.read()
        post = frontmatter.loads(content)
        return tokenize(post.content)


async def read_pdf(file: Path) -> list[str]:
    tokens = []

    reader = PdfReader(file.resolve())
    for page in reader.pages:
        tokens.extend(tokenize(page.extract_text()))

    return tokens


async def read_epub(file: Path) -> list[str]:
    tokens = []
    book = epub.read_epub(file, {"ignore_ncx": True})
    for page in book.get_items_of_type(ebooklib.ITEM_DOCUMENT):
        content = page.get_body_content().decode()
        tokens.extend(tokenize(content))

    return tokens


async def read_docx(file: Path) -> list[str]:
    tokens = []
    document = Document(f"{file}")
    for paragraph in document.paragraphs:
        tokens.extend(tokenize(paragraph.text))

    return tokens
