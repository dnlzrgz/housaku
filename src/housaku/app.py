from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from housaku.db import init_db
from housaku.settings import Settings
from housaku.search import search
from housaku.utils import tokenize

app = FastAPI()

settings = Settings()


@app.get("/search/{query}")
def get_search(query: str | None):
    engine = create_engine(settings.sqlite_url)
    init_db(engine)

    if not query:
        return {"query": query}

    tokens = tokenize(query)
    with Session(engine) as session:
        return search(session, tokens)
