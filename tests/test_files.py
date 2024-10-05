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
        uri, name, content = read_txt(test_file)
        assert uri == f"{test_file.resolve()}"
        assert name == test_file.name
        assert content


def test_read_csv():
    for test_file in TEST_FILES_DIR.glob("*.csv"):
        uri, name, content = read_txt(test_file)
        assert uri == f"{test_file.resolve()}"
        assert name == test_file.name
        assert content


def test_read_pdf():
    for test_file in TEST_FILES_DIR.glob("*.pdf"):
        uri, name, content = read_generic_doc(test_file)
        assert uri == f"{test_file.resolve()}"
        assert name == test_file.name
        assert content


def test_read_epub():
    for test_file in TEST_FILES_DIR.glob("*.epub"):
        uri, name, content = read_generic_doc(test_file)
        assert uri == f"{test_file.resolve()}"
        assert name == test_file.name
        assert content


def test_read_docx():
    for test_file in TEST_FILES_DIR.glob("*.docx"):
        uri, name, content = read_generic_doc(test_file)
        assert uri == f"{test_file.resolve()}"
        assert name == test_file.name
        assert content


def test_bench_list_files(benchmark):
    file_list = benchmark(list_files, TEST_FILES_DIR)
    assert file_list


def test_bench_read_txt(benchmark):
    test_file = TEST_FILES_DIR / "gutenberg_moby_dick.txt"
    uri, _, _ = benchmark(read_txt, test_file)
    assert uri


def test_bench_read_pdf(benchmark):
    test_file = TEST_FILES_DIR / "gutenberg_the_modern_prometheus.pdf"
    uri, _, _ = benchmark(read_generic_doc, test_file)
    assert uri


def test_bench_read_epub(benchmark):
    test_file = TEST_FILES_DIR / "fundamental_accessibility.epub"
    uri, _, _ = benchmark(read_generic_doc, test_file)
    assert uri
