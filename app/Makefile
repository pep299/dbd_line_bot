.PHONY: lint format test test-ci

lint:
	poetry run pysen run lint

format:
	poetry run pysen run format

test:
	poetry run pytest

test-ci:
	poetry run pytest --junitxml=pytest.xml --cov-report=term-missing --cov=src | tee pytest-coverage.txt
