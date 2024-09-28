from collections import deque
import fnmatch
import mimetypes
from pathlib import Path
from typing import is_typeddict
import pymupdf
from housaku.db import db_connection
from housaku.utils import console

GENERIC_FILETYPES = [
    "application/pdf",
    "application/epub+zip",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
]


def list_files(root: Path, exclude: list[str] = []) -> list[Path]:
    exclude_set = set(exclude)
    pending_dirs = deque([root])
    files = []

    if root.is_dir():
        while pending_dirs:
            dir = pending_dirs.popleft()
            for path in dir.iterdir():
                if any(fnmatch.fnmatch(path.name, pattern) for pattern in exclude_set):
                    continue

                if path.is_dir():
                    pending_dirs.append(path)

                if path.is_file():
                    files.append(path.resolve())
    else:
        if not any(fnmatch.fnmatch(root.name, pattern) for pattern in exclude_set):
            files.append(root.resolve())

    return files


def read_file(file: Path) -> tuple[str, str, str]:
    mime_type, _ = mimetypes.guess_type(file)

    if mime_type == "text/plain" or mime_type == "text/markdown":
        return read_txt(file)
    if mime_type in GENERIC_FILETYPES:
        return read_generic_doc(file)
    else:
        raise Exception(f"Unsupported file format {mime_type}")


def read_txt(file: Path) -> tuple[str, str, str]:
    with open(file, "r") as f:
        return f"{file.resolve()}", file.name, f.read()


def read_generic_doc(file: Path) -> tuple[str, str, str]:
    content = ""
    with pymupdf.open(file) as doc:
        for page in doc:
            content += page.get_text()

    return f"{file.resolve()}", file.name, content


def index_file(sqlite_url: str, file: Path) -> None:
    uri = f"{file}"
    try:
        uri, title, content = read_file(file)
        with db_connection(sqlite_url) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
            INSERT INTO documents (uri, title, type, content)
            VALUES (?, ?, ?, ?)
            """,
                (uri, title, "file", content),
            )
        console.print(f"[green][Ok][/] indexed '{file}'.")
    except Exception as e:
        console.print(f"[red][Err][/] something went wrong while reading '{file}': {e}")
