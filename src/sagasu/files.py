from pathlib import Path
import mimetypes
import fnmatch
from aiofile import async_open
from pypdf import PdfReader
import frontmatter
from sagasu.utils import tokenize


def list_files(root: Path, exclude: list[str] = []) -> set[Path]:
    if not root.is_dir():
        raise Exception(f"path '{root}' is not a directory")

    exclude_set = set(exclude)
    file_list = set()

    pending_dirs = [root]
    while pending_dirs:
        dir = pending_dirs.pop()
        for path in dir.iterdir():
            if any(fnmatch.fnmatch(path.name, pattern) for pattern in exclude_set):
                continue

            if path.is_dir():
                pending_dirs.append(path)

            if path.is_file():
                file_list.add(path.resolve())

    return file_list


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
