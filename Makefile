.PHONY: lint

lint:
	uvx black src
	uvx ruff check --fix src