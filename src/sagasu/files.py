from pathlib import Path
import mimetypes
import frontmatter
from sagasu.utils import tokenize


def list_files_in_dir(path: Path) -> list[Path]:
    if not path.is_dir():
        # TODO: raise
        print("Error: path provided is not a directoy")

    files = [file.resolve() for file in path.rglob("*") if file.is_file()]

    return files


def read_file(file: Path) -> tuple[str, list[str], dict] | None:
    mime_type, _ = mimetypes.guess_type(file)

    try:
        if mime_type == "text/plain":
            return _read_plain_text_file(file)
        if mime_type == "text/markdown":
            return _read_markdown_file(file)
        else:
            print(f"Unsupported file format {mime_type}")
    except Exception as e:
        print(f"Error reading file: {e}")


def _read_plain_text_file(file: Path) -> tuple[str, list[str], dict] | None:
    with file.open("r", encoding="utf-8") as f:
        content = f.read()
        return (content, tokenize(content), {})


def _read_markdown_file(file: Path) -> tuple[str, list[str], dict] | None:
    post = frontmatter.load(f"{file.resolve()}")
    return (post.content, tokenize(post.content), post.metadata)
