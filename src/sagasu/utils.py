import string
from sagasu.stop_words import STOP_WORDS

translation_table = str.maketrans(string.punctuation, " " * len(string.punctuation))


def normalize(text: str) -> list[str]:
    text = text.translate(translation_table)
    text = " ".join(text.lower().split())
    tokens = [token for token in text.split() if token not in STOP_WORDS]
    return tokens
