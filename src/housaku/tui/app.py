import textwrap
from time import perf_counter
import urllib.parse
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Container
from textual.widgets import Button, Input, ListItem, ListView, Static
from housaku.db import init_db
from housaku.files import FILETYPES_SET
from housaku.settings import Settings
from housaku.search import search


class HousakuApp(App):
    TITLE = "housaku"
    CSS_PATH = "global.tcss"
    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, settings: Settings):
        self.settings = settings
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Container(
            Static(f"{self.settings.name}", classes="about__title"),
            Static(f"{self.settings.version}", classes="about__version"),
            classes="about",
        )
        yield Horizontal(
            Input(placeholder="Search", type="text", classes="search__input"),
            Button(label="Search", classes="search__button"),
            classes="search",
        )
        yield ListView(classes="results")

    def on_mount(self) -> None:
        self.results = self.query_one(ListView)
        self.results.border_title = "results"

    @on(Input.Submitted)
    def handle_input(self, message: Input.Submitted) -> None:
        self.search_documents(message.value)

    def search_documents(self, query: str) -> None:
        self.results.loading = True
        self.results.clear()

        start_time = perf_counter()

        try:
            results = search(self.settings.sqlite_url, query, 10)
        except Exception as e:
            self.notify(
                f"[red][Err][/] Something went wrong with your query: {e}",
                severity="error",
            )
            self.results.loading = False
            return

        end_time = perf_counter()

        if not results:
            self.notify("No results found.", severity="warning")
            self.results.loading = False
            return

        for uri, title, doc_type, content in results:
            encoded_uri = urllib.parse.quote(uri, safe=":/")
            doc_title = title if title else uri
            truncated_content = textwrap.shorten(content, width=280, placeholder="...")

            if doc_type in FILETYPES_SET:
                link = f"[link=file://{encoded_uri}]{uri}[/]"
            else:
                link = f"[link={uri}]{uri}[/]"

            self.results.mount(
                ListItem(
                    Container(
                        Static(doc_title, classes="result__title"),
                        Static(link, classes="result__link"),
                        Static(truncated_content, classes="result__content"),
                        classes="result",
                    ),
                )
            )

        elapsed_time = end_time - start_time
        self.results.loading = False
        self.results.border_subtitle = f"in {elapsed_time:.3f}s"


if __name__ == "__main__":
    settings = Settings()
    init_db(settings.sqlite_url)

    app = HousakuApp(settings)
    app.run()
