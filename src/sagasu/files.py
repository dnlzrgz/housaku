from pathlib import Path
import mimetypes
from aiofile import async_open
from pypdf import PdfReader
import frontmatter
from sagasu.utils import tokenize


def list_files(path: Path) -> list[Path]:
    if not path.is_dir():
        raise Exception(f"Error: path {path} is not a directoy")

    return [file.resolve() for file in path.rglob("*") if file.is_file()]


async def extract_tokens(file: Path) -> list[str]:
    mime_type, _ = mimetypes.guess_type(file)

    if mime_type == "text/plain":
        return await read_txt(file)
    if mime_type == "text/markdown":
        return await read_md(file)
    if mime_type == "application/pdf":
        return await read_pdf(file)
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
