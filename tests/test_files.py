from pathlib import Path
from housaku.files import list_files, read_file, read_plain_text, read_complex

TEST_FILES_DIR = Path(__file__).parent / "examples"


def test_list_files():
    file_list = list_files(TEST_FILES_DIR)
    assert len(file_list) == sum(
        1 for item in TEST_FILES_DIR.iterdir() if item.is_file()
    )


def test_read_text_file():
    for test_file in TEST_FILES_DIR.glob("*.txt"):
        doc = read_file(test_file)
        assert doc.uri == f"{test_file.resolve()}"
        assert doc.title == test_file.name
        assert doc.body


def test_read_csv_file():
    for test_file in TEST_FILES_DIR.glob("*.csv"):
        doc = read_file(test_file)
        assert doc.uri == f"{test_file.resolve()}"
        assert doc.title == test_file.name
        assert doc.body


def test_read_pdf_file():
    for test_file in TEST_FILES_DIR.glob("*.pdf"):
        doc = read_file(test_file)
        assert doc.uri == f"{test_file.resolve()}"
        assert doc.title == test_file.name
        assert doc.body


def test_read_epub_file():
    for test_file in TEST_FILES_DIR.glob("*.epub"):
        doc = read_file(test_file)
        assert doc.uri == f"{test_file.resolve()}"
        assert doc.title == test_file.name
        assert doc.body


def test_read_docx_file():
    for test_file in TEST_FILES_DIR.glob("*.docx"):
        doc = read_file(test_file)
        assert doc.uri == f"{test_file.resolve()}"
        assert doc.title == test_file.name
        assert doc.body


def test_bench_list_files(benchmark):
    file_list = benchmark(list_files, TEST_FILES_DIR)
    assert file_list


def test_bench_read_text_file(benchmark):
    test_file = TEST_FILES_DIR / "gutenberg_moby_dick.txt"
    body = benchmark(read_plain_text, test_file)
    assert body


def test_bench_read_pdf_file(benchmark):
    test_file = TEST_FILES_DIR / "gutenberg_the_modern_prometheus.pdf"
    body = benchmark(read_complex, test_file)
    assert body


def test_bench_read_epub_file(benchmark):
    test_file = TEST_FILES_DIR / "fundamental_accessibility.epub"
    body = benchmark(read_complex, test_file)
    assert body
