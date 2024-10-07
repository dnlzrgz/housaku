import textwrap
from time import perf_counter
import urllib.parse
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Container
from textual.reactive import reactive
from textual.validation import ValidationResult, Validator
from textual.widgets import Button, Footer, Input, ListItem, ListView, Static
from housaku.db import init_db
from housaku.files import FILETYPES_SET
from housaku.settings import Settings
from housaku.search import search


class SearchInputValidator(Validator):
    def validate(self, value: str) -> ValidationResult:
        return (
            self.success()
            if value
            else self.failure("Search query cannot be an empty string.")
        )


class HousakuApp(App):
    TITLE = "housaku"
    CSS_PATH = "global.tcss"
    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", priority=True),
    ]

    search_query: reactive[str] = reactive("")

    def __init__(self, settings: Settings):
        self.settings = settings
        super().__init__()

    def compose(self) -> ComposeResult:
        yield Container(
            Static(
                f"{self.settings.name}",
                classes="about__title",
            ),
            Static(
                f"{self.settings.version}",
                classes="about__version",
            ),
            classes="about",
        )
        yield Horizontal(
            Input(
                placeholder="Search",
                type="text",
                classes="search__input",
                validate_on=["submitted"],
                validators=[SearchInputValidator()],
            ),
            Button(
                label="Search",
                classes="search__button",
                disabled=True,
            ),
            classes="search",
        )
        yield ListView(classes="results")
        yield Footer(classes="footer")

    def on_mount(self) -> None:
        self.input_field = self.query_one(Input)
        self.search_button = self.query_one(Button)

        self.results = self.query_one(ListView)
        self.results.border_title = "results"

    @on(Input.Submitted)
    @on(Button.Pressed, selector=".search__button")
    def handle_submit(self, _: Input.Submitted | Button.Pressed) -> None:
        if not self.input_field.is_valid:
            self.notify(
                "Search query cannot be empty.",
                severity="error",
            )
            return

        self.search_documents(self.search_query)

    @on(Input.Changed)
    def handle_change_input(self, event: Input.Changed) -> None:
        self.search_query = event.value

    def watch_search_query(self, value: str) -> None:
        if value:
            self.search_button.disabled = False
        else:
            self.search_button.disabled = True

    def search_documents(self, query: str) -> None:
        self.results.loading = True
        self.results.clear()

        start_time = perf_counter()

        try:
            results = search(self.settings.sqlite_url, query, 10)
        except Exception as e:
            self.notify(
                f"Something went wrong with your query: {e}.",
                severity="error",
            )
            self.results.loading = False
            return

        end_time = perf_counter()

        if not results:
            self.notify(
                "No results found.",
                severity="warning",
            )
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
                    Static(doc_title, classes="result__title"),
                    Static(link, classes="result__link"),
                    Static(truncated_content, classes="result__content"),
                    classes="result",
                )
            )

        elapsed_time = end_time - start_time
        self.results.loading = False
        self.results.focus()
        self.results.index = 0
        self.results.border_subtitle = f"in {elapsed_time:.3f}s"


if __name__ == "__main__":
    settings = Settings()
    init_db(settings.sqlite_url)

    app = HousakuApp(settings)
    app.run()
