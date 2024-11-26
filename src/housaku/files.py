from pathlib import Path
import fnmatch
from collections import deque
import pymupdf
from housaku.models import Doc
from housaku.db import with_db
from housaku.utils import console

PLAIN_TEXT_EXTENSIONS = {".txt", ".md", ".csv"}
COMPLEX_DOCUMENT_EXTENSIONS = {".pdf", ".epub", ".docx", ".pptx", ".xlsx"}
SUPPORTED_EXTENSIONS = PLAIN_TEXT_EXTENSIONS.union(COMPLEX_DOCUMENT_EXTENSIONS)

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
    doc_type = file.suffix
    if doc_type in PLAIN_TEXT_EXTENSIONS:
        body = read_plain_text(file)
    elif doc_type in COMPLEX_DOCUMENT_EXTENSIONS:
        body = read_complex(file)
    else:
        raise Exception(f'Unsupported file format "{file.suffix}"')

    return Doc(
        uri=f"{file.resolve()}",
        title=file.name,
        body=body,
        doc_type=doc_type,
    )


def read_plain_text(file: Path) -> str:
    with open(file, "r") as f:
        return f.read()


def read_complex(file: Path) -> str:
    body = ""
    with pymupdf.open(file) as doc:
        for page in doc:
            body += page.get_text()

    return body


def index_file(sqlite_url: str, file: Path) -> None:
    try:
        with with_db(sqlite_url) as conn:
            cursor = conn.cursor()

            cursor.execute(
                "SELECT last_modified FROM documents WHERE uri = ?",
                (f"{file.resolve()}",),
            )
            result = cursor.fetchone()
            new_last_modified = round(file.stat().st_mtime, 3)

            if result:
                current_last_modified = float(result[0])

                if current_last_modified == new_last_modified:
                    console.print(f'[yellow][Skip][/] already indexed "{file}".')
                    return
                else:
                    doc = read_file(file)
                    cursor.execute(
                        """
                    UPDATE documents
                    SET body = ?, last_modified = ?
                    WHERE uri = ?
                        """,
                        (doc.body, new_last_modified, doc.uri),
                    )
                    console.print(f'[yellow][Update][/] updated modified "{file}".')
            else:
                doc = read_file(file)
                cursor.execute(
                    """
            INSERT INTO documents (uri, title, type, body, last_modified)
            VALUES (?, ?, ?, ?, ?)
            """,
                    (
                        doc.uri,
                        doc.title,
                        doc.doc_type,
                        doc.body,
                        new_last_modified,
                    ),
                )
                console.print(f'[green][Ok][/] indexed "{file}".')
    except Exception as e:
        console.print(f'[red][Err][/] something went wrong while reading "{file}": {e}')
