from pathlib import Path
from housaku.files import list_files, read_txt, read_generic_doc

TEST_FILES_DIR = Path(__file__).parent / "examples"


def test_list_files():
    file_list = list_files(TEST_FILES_DIR)
    assert len(file_list) == sum(
        1 for item in TEST_FILES_DIR.iterdir() if item.is_file()
    )


def test_read_txt():
    for test_file in TEST_FILES_DIR.glob("*.txt"):
        doc = read_txt(test_file)
        assert doc.uri == f"{test_file.resolve()}"
        assert doc.title == test_file.name
        assert doc.body


def test_read_csv():
    for test_file in TEST_FILES_DIR.glob("*.csv"):
        doc = read_txt(test_file)
        assert doc.uri == f"{test_file.resolve()}"
        assert doc.title == test_file.name
        assert doc.body


def test_read_pdf():
    for test_file in TEST_FILES_DIR.glob("*.pdf"):
        doc = read_generic_doc(test_file)
        assert doc.uri == f"{test_file.resolve()}"
        assert doc.title == test_file.name
        assert doc.body


def test_read_epub():
    for test_file in TEST_FILES_DIR.glob("*.epub"):
        doc = read_generic_doc(test_file)
        assert doc.uri == f"{test_file.resolve()}"
        assert doc.title == test_file.name
        assert doc.body


def test_read_docx():
    for test_file in TEST_FILES_DIR.glob("*.docx"):
        doc = read_generic_doc(test_file)
        assert doc.uri == f"{test_file.resolve()}"
        assert doc.title == test_file.name
        assert doc.body


def test_bench_list_files(benchmark):
    file_list = benchmark(list_files, TEST_FILES_DIR)
    assert file_list


def test_bench_read_txt(benchmark):
    test_file = TEST_FILES_DIR / "gutenberg_moby_dick.txt"
    doc = benchmark(read_txt, test_file)
    assert doc.uri


def test_bench_read_pdf(benchmark):
    test_file = TEST_FILES_DIR / "gutenberg_the_modern_prometheus.pdf"
    doc = benchmark(read_generic_doc, test_file)
    assert doc.uri


def test_bench_read_epub(benchmark):
    test_file = TEST_FILES_DIR / "fundamental_accessibility.epub"
    doc = benchmark(read_generic_doc, test_file)
    assert doc.uri
