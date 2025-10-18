.PHONY: lint

lint:
	uvx ruff check --fix src
	uvx ruff format src