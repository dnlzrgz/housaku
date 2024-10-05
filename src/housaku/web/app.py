from pathlib import Path
from typing import Annotated
from fastapi import FastAPI, Request, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from housaku.db import init_db
from housaku.settings import Settings
from housaku.search import search

settings = Settings()
init_db(settings.sqlite_url)

app = FastAPI()

base_dir = Path(__file__).resolve().parent
app.mount("/static", StaticFiles(directory=base_dir / "static"), name="static")
templates = Jinja2Templates(directory=base_dir / "templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={})


@app.post("/search/", response_class=HTMLResponse)
async def search_results(request: Request, query: Annotated[str, Form()]):
    try:
        results = search(settings.sqlite_url, query)
    except Exception as e:
        return 404, {"detail": f"{e}"}

    return templates.TemplateResponse(
        request=request,
        name="results.html",
        context={"query": query, "results": results},
    )
