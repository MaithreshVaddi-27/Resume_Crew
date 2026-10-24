# Resume_Crew — development shortcuts
#
#   make setup     create venv + install deps
#   make test      run the test suite
#   make lint      run ruff check + format check
#   make fmt       run ruff format + fix
#   make typecheck run mypy
#   make ui        launch the Gradio web UI
#   make cli       run the CLI on the bundled samples

.PHONY: setup test lint fmt typecheck ui cli clean

PY ?= python3

setup:
	$(PY) -m venv venv
	venv/bin/python -m pip install --upgrade pip
	venv/bin/python -m pip install -e '.[dev]'

test:
	$(PY) -m pytest

lint:
	ruff check src tests
	ruff format --check src tests

fmt:
	ruff check --fix src tests
	ruff format src tests

typecheck:
	mypy --config-file pyproject.toml src

ui:
	python app.py

cli:
	python main.py --resume samples/Resumes/sample_resume.pdf --job-description samples/Job_description/sample_job_description.pdf --provider ollama

clean:
	rm -rf venv .pytest_cache __pycache__ src/**/__pycache__ *.egg-info dist build .ruff_cache .mypy_cache
