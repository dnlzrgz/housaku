search:
	uv run sagasu search

index:
	uv run sagasu index

app:
	uv run sagasu app

test:
	pytest -v

test-files:
	pytest tests/test_files.py

test-repos:
	pytest tests/test_repositories.py

test-search:
	pytest tests/test_search.py

test-utils:
	pytest tests/test_utils.py

lint:
	uv run ruff check --fix
