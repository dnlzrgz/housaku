import textwrap
from time import perf_counter
import urllib.parse
from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Container
from textual.reactive import reactive
from textual.validation import Number, ValidationResult, Validator
from textual.widgets import (
    Button,
    Footer,
    Input,
    Label,
    ListItem,
    ListView,
    Static,
)
from housaku.db import init_db
from housaku.files import SUPPORTED_EXTENSIONS
from housaku.settings import Settings
from housaku.search import search


class SearchInputValidator(Validator):
    def validate(self, value: str) -> ValidationResult:
        return (
            self.success()
            if value
            else self.failure("Search query cannot be an empty string.")
        )


class ItemMetadata(Static):
    def __init__(self, link: str, *args, **kwargs) -> None:
        self.link = link
        super().__init__(*args, **kwargs)


class HousakuApp(App):
    TITLE = "housaku"
    CSS_PATH = "global.tcss"
    ENABLE_COMMAND_PALETTE = False

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", priority=True),
    ]

    search_query: reactive[str] = reactive("")
    max_results: reactive[int] = reactive(10)

    def __init__(self, settings: Settings):
        super().__init__()

        self.settings = settings
        self.theme = self.settings.theme

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
            Container(
                Label("query", classes="query__label"),
                Input(
                    placeholder="Search",
                    type="text",
                    classes="query__input",
                    validate_on=["submitted"],
                    validators=[SearchInputValidator()],
                ),
                classes="query",
            ),
            Container(
                Label("#", classes="nresults__label"),
                Input(
                    type="integer",
                    value=f"{self.max_results}",
                    placeholder="10",
                    validators=Number(minimum=1),
                    classes="nresults__input",
                ),
                classes="nresults",
            ),
            Button(
                label="Search",
                classes="submit",
            ),
            classes="search",
        )
        yield ListView(classes="results")
        yield Footer(classes="footer")

    def on_mount(self) -> None:
        self.query_input = self.query_one(".query__input")
        self.submit_button = self.query_one(".submit")

        self.results = self.query_one(".results")
        self.results.border_title = "results"

        self.query_input.focus()

    @on(Input.Submitted)
    @on(Button.Pressed, selector=".submit")
    async def handle_submit(self, _: Input.Submitted | Button.Pressed) -> None:
        if not self.query_input.is_valid:
            self.notify(
                "Search query cannot be empty.",
                severity="error",
            )
            return

        await self._search()

    @on(Input.Changed, selector=".query__input")
    def update_search_query(self, event: Input.Changed) -> None:
        self.search_query = event.value

    @on(Input.Changed, selector=".nresults__input")
    def update_max_results(self, event: Input.Changed) -> None:
        try:
            self.max_results = int(event.value)
        except Exception:
            self.max_results = 10

    @on(ListView.Selected)
    def open_search_result(self, event: ListView.Selected) -> None:
        link = event.item.query_exactly_one(ItemMetadata).link
        self.open_url(link)

    async def _search(self) -> None:
        self.results.clear()
        self.results.loading = True
        start_time = perf_counter()

        try:
            documents = search(
                self.settings.sqlite_url, self.search_query, self.max_results
            )
        except Exception as e:
            self.notify(
                f"Something went wrong with your query: {e}.",
                severity="error",
            )
            self.results.loading = False
            return

        end_time = perf_counter()

        if not documents:
            self.notify(
                "No results found.",
                severity="warning",
            )
            self.results.loading = False
            return

        for uri, title, doc_type, content in documents:
            encoded_uri = urllib.parse.quote(uri, safe=":/")
            doc_title = title if title else uri
            truncated_content = textwrap.shorten(content, width=280, placeholder="...")

            if doc_type in SUPPORTED_EXTENSIONS:
                link = f"[link=file://{encoded_uri}]{uri}[/]"
            else:
                link = f"[link={uri}]{uri}[/]"

            self.results.mount(
                ListItem(
                    Container(Static(doc_type), classes="result__type"),
                    Container(
                        Static(doc_title, classes="result__title"),
                        Static(link, classes="result__link"),
                        Static(truncated_content, classes="result__content"),
                        ItemMetadata(encoded_uri),
                    ),
                    classes="result",
                )
            )

        elapsed_time = end_time - start_time
        self.results.loading = False
        self.results.focus()
        self.results.index = 0
        self.results.border_subtitle = (
            f"Found {len(documents)} results in {elapsed_time:.3f}s"
        )


if __name__ == "__main__":
    settings = Settings()
    init_db(settings.sqlite_url)

    app = HousakuApp(settings)
    app.run()
