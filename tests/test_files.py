from sagasu.files import read_file
from sagasu.utils import tokenize


CONTENT = "Time is an illusion. Lunchtime doubly so."


def test_read_text_file(tmp_path):
    temp_file = tmp_path / "guide.txt"
    temp_file.write_text(CONTENT)

    result = read_file(temp_file)
    assert result is not None

    content, words = result
    assert content == CONTENT
    assert len(words) == len(tokenize(CONTENT))
