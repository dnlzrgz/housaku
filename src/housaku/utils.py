import string
from selectolax.parser import HTMLParser
from housaku.stop_words import STOP_WORDS

translation_table = str.maketrans(string.punctuation, " " * len(string.punctuation))


def tokenize(text: str) -> list[str]:
    tokens = text.lower().translate(translation_table).split()
    tokens = [
        token for token in tokens if token not in STOP_WORDS and not token[0].isdigit()
    ]
    return tokens


def clean_html(html: str) -> str:
    tree = HTMLParser(html)
    for tag in tree.css("script, style, video, img, canvas"):
        tag.decompose()

    text = "".join(node.text(deep=True) for node in tree.css("main"))
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split(" "))
    cleaned_text = " ".join(chunk for chunk in chunks if chunk)

    return cleaned_text
