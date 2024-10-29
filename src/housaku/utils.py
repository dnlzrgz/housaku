from rich.console import Console
from selectolax.parser import HTMLParser

console = Console()


def clean_html(html: str) -> str:
    tree = HTMLParser(html)
    for tag in tree.css("script, style, video, img, canvas"):
        tag.decompose()

    text = "".join(node.text(deep=True) for node in tree.css("main"))
    lines = (line.strip() for line in text.splitlines())
    chunks = (phrase.strip() for line in lines for phrase in line.split(" "))
    cleaned_text = " ".join(chunk for chunk in chunks if chunk)

    return cleaned_text
