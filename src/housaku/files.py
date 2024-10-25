from pathlib import Path
import fnmatch
import mimetypes
from collections import deque
import pymupdf
from housaku.models import Doc
from housaku.db import with_db
from housaku.utils import console, get_content_digest

PLAIN_TEXT_FILETYPES = {
    "text/plain",
    "text/markdown",
    "text/csv",
}

COMPLEX_DOCUMENT_FILETYPES = {
    "application/pdf",
    "application/epub+zip",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}

FILETYPES_SET = PLAIN_TEXT_FILETYPES.union(COMPLEX_DOCUMENT_FILETYPES)

pymupdf.JM_mupdf_show_errors = 0


def list_files(root: Path, exclude: set[str] = set()) -> list[Path]:
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


def read_file(file: Path) -> Doc:
    mime_type, _ = mimetypes.guess_type(file)

    if mime_type in PLAIN_TEXT_FILETYPES:
        doc = read_txt(file)
    elif mime_type in COMPLEX_DOCUMENT_FILETYPES:
        doc = read_generic_doc(file)
    else:
        raise Exception(f"Unsupported file format {mime_type}")

    doc.doc_type = mime_type
    return doc


def read_txt(file: Path) -> Doc:
    with open(file, "r") as f:
        return Doc(
            uri=f"{file.resolve()}",
            title=file.name,
            body=f.read(),
        )


def read_generic_doc(file: Path) -> Doc:
    body = ""
    with pymupdf.open(file) as doc:
        for page in doc:
            body += page.get_text()

    return Doc(
        uri=f"{file.resolve()}",
        title=file.name,
        body=body,
    )


def index_file(sqlite_url: str, file: Path) -> None:
    try:
        with with_db(sqlite_url) as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT hash FROM documents WHERE uri = ?",
                (f"{file.resolve()}",),
            )
            result = cursor.fetchone()
            new_hash = get_content_digest(file)

            if result:
                exiting_hash = result[0]

                if exiting_hash == new_hash:
                    console.print(f"[yellow][Skip][/] already indexed '{file}'.")
                    return
                else:
                    doc = read_file(file)
                    cursor.execute(
                        """
                    UPDATE documents
                    SET body = ?, hash = ?
                    WHERE uri = ?
                        """,
                        (doc.body, new_hash, doc.uri),
                    )
                    console.print(f"[yellow][Update][/] updated modified '{file}'.")
            else:
                doc = read_file(file)
                cursor.execute(
                    """
            INSERT INTO documents (uri, title, type, body, hash)
            VALUES (?, ?, ?, ?, ?)
            """,
                    (doc.uri, doc.title, doc.doc_type, doc.body, new_hash),
                )
                console.print(f"[green][Ok][/] indexed '{file}'.")
    except Exception as e:
        console.print(f"[red][Err][/] something went wrong while reading '{file}': {e}")
