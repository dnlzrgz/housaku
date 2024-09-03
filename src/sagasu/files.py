from pathlib import Path
import mimetypes
from aiofile import async_open
import frontmatter
from sagasu.utils import tokenize


def list_files_in_dir(path: Path) -> list[Path] | None:
    if not path.is_dir():
        # TODO: raise
        print("Error: path provided is not a directoy")
        return None

    files = [file.resolve() for file in path.rglob("*") if file.is_file()]

    return files


async def read_file(file: Path) -> tuple[str, list[str], dict] | None:
    mime_type, _ = mimetypes.guess_type(file)

    try:
        if mime_type == "text/plain":
            return await _read_plain_text_file(file)
        if mime_type == "text/markdown":
            return await _read_markdown_file(file)
        else:
            print(f"Unsupported file format {mime_type}")
    except Exception as e:
        print(f"Error reading file: {e}")


async def _read_plain_text_file(file: Path) -> tuple[str, list[str], dict] | None:
    async with async_open(file, "r") as af:
        content = await af.read()
        return (content, tokenize(content), {})


async def _read_markdown_file(file: Path) -> tuple[str, list[str], dict] | None:
    async with async_open(file, "r") as af:
        content = await af.read()
        post = frontmatter.loads(content)
        return (post.content, tokenize(post.content), {})
