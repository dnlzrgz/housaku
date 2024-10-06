clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete

lint:
	uv run ruff check . --fix

update:
	uv lock --upgrade
	uv sync

index:
	uv run housaku index

search:
	uv run housaku search

web:
	uv run housaku web

web-dev:
	uv run fastapi dev src/housaku/web/app.py

tui:
	uv run housaku tui

tui-dev:
	uv run textual run --dev src/housaku/tui/app.py

test:
	pytest -v
