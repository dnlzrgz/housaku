import pytest
from pathlib import Path
from housaku.files import list_files, read_txt, read_md, read_pdf, read_generic_doc

TEST_FILES_DIR = Path(__file__).parent / "examples"


def test_list_files():
    file_list = list(list_files(TEST_FILES_DIR))
    assert len(file_list) == sum(
        1 for item in TEST_FILES_DIR.iterdir() if item.is_file()
    )


@pytest.mark.asyncio
async def test_read_txt():
    for test_file in TEST_FILES_DIR.glob("*.txt"):
        page = await read_txt(test_file)

        assert page.uri == f"{test_file.resolve()}"
        assert len(page.tokens)
        assert page.properties


@pytest.mark.asyncio
async def test_read_md():
    for test_file in TEST_FILES_DIR.glob("*.md"):
        page = await read_md(test_file)

        assert page.uri == f"{test_file.resolve()}"
        assert len(page.tokens)
        assert page.properties


@pytest.mark.asyncio
async def test_read_pdf():
    for test_file in TEST_FILES_DIR.glob("*.pdf"):
        async for page in read_pdf(test_file):
            assert page.uri
            assert page.properties


@pytest.mark.asyncio
async def test_read_epub():
    for test_file in TEST_FILES_DIR.glob("*.epub"):
        page = await read_generic_doc(test_file)

        assert page.uri == f"{test_file.resolve()}"
        assert len(page.tokens)
        assert page.properties


@pytest.mark.asyncio
async def test_read_docx():
    for test_file in TEST_FILES_DIR.glob("*.docx"):
        page = await read_generic_doc(test_file)

        assert page.uri == f"{test_file.resolve()}"
        assert len(page.tokens)
        assert page.properties


def test_bench_list_files(benchmark):
    file_list = benchmark(list_files, TEST_FILES_DIR)
    assert file_list


@pytest.mark.asyncio
async def test_bench_read_txt(benchmark):
    test_file = TEST_FILES_DIR / "gutenberg_moby_dick.txt"
    page = await benchmark(read_txt, test_file)

    assert page.uri == f"{test_file.resolve()}"


@pytest.mark.asyncio
async def test_bench_read_md(benchmark):
    test_file = TEST_FILES_DIR / "daring_fireball_markdown_syntax.md"
    page = await benchmark(read_md, test_file)

    assert page.uri == f"{test_file.resolve()}"


@pytest.mark.asyncio
async def test_bench_read_pdf(benchmark):
    test_file = TEST_FILES_DIR / "gutenberg_the_modern_prometheus.pdf"
    async for page in benchmark(read_pdf, test_file):
        assert page.uri


@pytest.mark.asyncio
async def test_bench_read_epub(benchmark):
    test_file = TEST_FILES_DIR / "fundamental_accessibility.epub"
    page = await benchmark(read_generic_doc, test_file)

    assert page.uri == f"{test_file.resolve()}"
