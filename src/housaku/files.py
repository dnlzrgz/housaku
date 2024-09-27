import fnmatch
import mimetypes
import os
from collections import deque, Counter
from datetime import datetime
from pathlib import Path
import frontmatter
import pymupdf
from sqlalchemy.orm import Session
from housaku.models import Doc, Posting, Word
from housaku.repositories import DocRepository, PostingRepository, WordRepository
from housaku.utils import get_digest, tokenize, console

GENERIC_FILETYPES = [
    "application/pdf",
    "application/epub+zip",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
]


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


def extract_tokens(file: Path) -> tuple[dict, list[str]]:
    mime_type, _ = mimetypes.guess_type(file)

    if mime_type == "text/plain":
        return read_txt(file)
    if mime_type == "text/markdown":
        return read_md(file)
    if mime_type in GENERIC_FILETYPES:
        return read_generic_doc(file)
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


def read_txt(file: Path) -> tuple[dict, list[str]]:
    metadata = get_file_metadata(file)

    with open(file, "r") as f:
        return metadata, tokenize(f.read())


def read_md(file: Path) -> tuple[dict, list[str]]:
    metadata = get_file_metadata(file)

    with open(file, "r") as f:
        post = frontmatter.loads(f.read())

    return (
        metadata | {key: str(value) for key, value in post.metadata.items()},
        tokenize(post.content),
    )


def read_generic_doc(file: Path) -> tuple[dict, list[str]]:
    metadata = get_file_metadata(file)

    tokens = []
    with pymupdf.open(file) as doc:
        for page in doc:
            tokens.extend(tokenize(page.get_text()))

    return metadata | doc.metadata, tokens


def index_file(session: Session, file: Path) -> None:
    doc_repo = DocRepository(session)
    posting_repo = PostingRepository(session)
    word_repo = WordRepository(session)

    uri = f"{file}"
    try:
        doc_in_db = doc_repo.get_by_attributes(uri=uri)
        content_hash = get_digest(file)
        metadata, tokens = extract_tokens(file)

        if not doc_in_db:
            doc_in_db = doc_repo.add(
                Doc(
                    uri=uri,
                    content_hash=content_hash,
                    properties=metadata,
                )
            )
        else:
            if doc_in_db.content_hash == content_hash:
                console.print(f"[yellow][Skip][/] file already indexed: '{uri}'")
                return
            else:
                console.print(f"[green][Update][/] updating file '{uri}'")
                postings = posting_repo.get_all_by_attributes(doc_id=doc_in_db.id)

                if postings:
                    for posting in postings:
                        posting_repo.delete(posting.id)

                    session.commit()

                doc_repo.update(doc_in_db.id, content_hash=content_hash)

        token_count = Counter(tokens)
        for token, count in token_count.items():
            word_in_db = word_repo.get_by_attributes(word=token)
            if not word_in_db:
                word_in_db = word_repo.add(Word(word=token))

            posting_in_db = posting_repo.get_by_attributes(
                word_id=word_in_db.id,
                doc_id=doc_in_db.id,
            )

            if not posting_in_db:
                posting_in_db = posting_repo.add(
                    Posting(
                        word=word_in_db,
                        doc=doc_in_db,
                        count=count,
                        tf=count / len(tokens),
                    )
                )

        session.commit()
        console.print(f"[green][Ok][/] indexed '{file}'.")
    except Exception as e:
        session.rollback()
        console.print(f"[red][Err][/] something went wrong while reading '{file}': {e}")
