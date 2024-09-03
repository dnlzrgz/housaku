import string
from sagasu.stop_words import STOP_WORDS

translation_table = str.maketrans(string.punctuation, " " * len(string.punctuation))


def tokenize(text: str) -> list[str]:
    tokens = text.lower().translate(translation_table).split()
    tokens = [
        token for token in tokens if token not in STOP_WORDS and not token[0].isdigit()
    ]
    return tokens
