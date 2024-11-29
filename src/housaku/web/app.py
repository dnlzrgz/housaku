from pathlib import Path
from starlette.applications import Starlette
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles
from starlette.responses import HTMLResponse, JSONResponse
from housaku.db import init_db
from housaku.settings import Settings
from housaku.search import search

settings = Settings()
init_db(settings.sqlite_url)

base_dir = Path(__file__).resolve().parent


async def homepage(_):
    index_page = base_dir / "index.html"
    return HTMLResponse(index_page.open().read())


async def search_results(request):
    data = await request.json()
    query = data["query"]
    try:
        results = search(settings.sqlite_url, query, 100)
        return JSONResponse(
            {
                "query": query,
                "results": results,
            }
        )
    except Exception as e:
        return 404, {"detail": f"{e}"}


routes = [
    Route("/", homepage, methods=["GET"]),
    Route("/search", search_results, methods=["POST"]),
    Mount("/static", app=StaticFiles(directory=base_dir / "static"), name="static"),
]


app = Starlette(routes=routes)
