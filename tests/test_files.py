from pathlib import Path
from sagasu.files import _read_plain_text_file, _read_markdown_file

TEST_FILES_DIR = Path(__file__).parent / "samples"


def test_read_plain_text_file():
    test_file = TEST_FILES_DIR / "short.txt"

    result = _read_plain_text_file(test_file)
    assert result is not None


def test_markdown_file():
    test_file = TEST_FILES_DIR / "short.md"

    result = _read_markdown_file(test_file)
    assert result is not None
