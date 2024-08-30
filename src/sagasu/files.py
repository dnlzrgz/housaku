from pathlib import Path
import mimetypes
from sagasu.utils import normalize


def list_files_in_dir(path: Path) -> list[Path]:
    if not path.is_dir():
        # TODO: raise
        print("Error: path provided is not a directoy")

    files = [file.resolve() for file in path.rglob("*") if file.is_file()]

    return files


def read_file(file: Path) -> tuple[str, list[str]] | None:
    mime_type, _ = mimetypes.guess_type(file)

    try:
        if mime_type == "text/plain":
            with file.open("r", encoding="utf-8") as f:
                content = f.read()
                return (content, normalize(content))
        else:
            print(f"Unsupported file format {mime_type}")
    except Exception as e:
        print(f"Error reading file: {e}")
