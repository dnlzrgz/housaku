import textwrap
import urllib.parse
from time import perf_counter
import rich_click as click
from housaku.files import SUPPORTED_EXTENSIONS
from housaku.search import search
from housaku.utils import console


@click.command(
    name="search",
    short_help="Search for documents and posts.",
)
@click.option(
    "-q",
    "--query",
    prompt="Search terms",
    help="Search terms to find relevant documents.",
)
@click.option(
    "-l",
    "--limit",
    type=int,
    default=10,
    help="Limit the number of documents returned.",
)
@click.pass_context
def search_documents(ctx: click.Context, query: str, limit: int) -> None:
    settings = ctx.obj["settings"]
    start_time = perf_counter()

    try:
        results = search(settings.sqlite_url, query, limit)
    except Exception as e:
        console.print(f"[red][Err][/] Something went wrong with your query: {e}")
        return

    if not results:
        console.print("[yellow]No results found.[/]")
        return

    end_time = perf_counter()
    elapsed_time = end_time - start_time

    for uri, title, doc_type, content in results:
        encoded_uri = urllib.parse.quote(uri, safe=":/")
        doc_title = title if title else uri

        truncated_content = textwrap.shorten(content, width=280, placeholder="...")
        link = f"[link={uri}]{doc_title}[/]"
        if doc_type in SUPPORTED_EXTENSIONS:
            link = f"[link=file://{encoded_uri}]{doc_title}[/]"

        console.print(
            f"{doc_type} [bold underline]{link}[/]\n{truncated_content}",
            justify="left",
            highlight=False,
            end="\n\n",
        )

    console.print(
        f"Search completed in {elapsed_time:.3f}s",
        highlight=False,
    )
