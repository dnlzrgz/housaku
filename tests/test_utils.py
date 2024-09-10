import pytest
from housaku.utils import tokenize


@pytest.fixture
def short_text() -> str:
    return """
    Far out in the uncharted backwaters of the unfasionable end of
    the western spiral arm of the Galaxy lies a small, unregarded yellow sun.
    """


@pytest.fixture
def medium_text() -> str:
    return """
    A towel, [The Hitchhiker's Guide to the Galaxy] says, is about the most
    massively useful thing an interstellar hitchhiker can have. Partly it
    has great practical value. You can wrap it around you for warmth as you
    bound across the cold moons of Jaglan Beta; you can lie on it on the brilliant
    marble-sanded beaches of Santraginus V, inhaling the heady sea vapors; you
    can sleep under it beneath the stars which shine so redly on the desert
    world of Kakrafoon; use it to sail a miniraft down the slow heavy
    River Moth; wet it for use in hand-to-hand-combat; wrap it round your
    head to ward off noxious fumes or avoid the gaze of the
    Ravenous Bugblatter Beast of Traal (such a mind-boggingly stupid
    animal, it assumes that if you can't see it, it can't
    see you); you can wave your towel in emergencies as a distress
    signal, and of course dry yourself off with it if it still seems
    to be clean enough.
    """


@pytest.fixture
def long_text(medium_text) -> str:
    return medium_text * 10


@pytest.mark.parametrize(
    "input, expected",
    [
        ("Hello, world!", ["world"]),
        ("This is a test", ["test"]),
        ("", []),
        ("\tThe\n\n\n", []),
    ],
)
def test_no_stop_words_after_tokenization(input, expected):
    assert tokenize(input) == expected


def test_bench_tokenize_small_text(short_text, benchmark):
    result = benchmark(tokenize, short_text)
    assert result


def test_bench_tokenize_medium_text(medium_text, benchmark):
    result = benchmark(tokenize, medium_text)
    assert result


def test_bench_tokenize_long_text(long_text, benchmark):
    result = benchmark(tokenize, long_text)
    assert result
