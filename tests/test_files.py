import pytest
from pathlib import Path
from sagasu.files import read_txt, read_md, read_pdf

TEST_FILES_DIR = Path(__file__).parent / "examples"


@pytest.mark.asyncio
async def test_read_txt():
    for test_file in TEST_FILES_DIR.glob("*.txt"):
        tokens = await read_txt(test_file)
        assert len(tokens) > 0


@pytest.mark.asyncio
async def test_read_md():
    for test_file in TEST_FILES_DIR.glob("*.md"):
        tokens = await read_md(test_file)
        assert len(tokens) > 0


@pytest.mark.asyncio
async def test_read_pdf():
    for test_file in TEST_FILES_DIR.glob("*.pdf"):
        tokens = await read_pdf(test_file)
        assert len(tokens) > 0


@pytest.mark.asyncio
async def test_bench_read_txt(benchmark):
    test_file = TEST_FILES_DIR / "gutenberg_moby_dick.txt"
    result = await benchmark(read_txt, test_file)
    assert result


@pytest.mark.asyncio
async def test_bench_read_md(benchmark):
    test_file = TEST_FILES_DIR / "daring_fireball_markdown_syntax.md"
    result = await benchmark(read_md, test_file)
    assert result


@pytest.mark.asyncio
async def test_bench_read_pdf(benchmark):
    test_file = TEST_FILES_DIR / "gutenberg_the_modern_prometheus.pdf"
    result = await benchmark(read_pdf, test_file)
    assert result
