-include .env
export

.PHONY: lint
lint:
	@poetry run ruff check .
	@poetry run ruff format --check .
	@poetry run basedpyright
	@poetry run docformatter --check --recursive .

.PHONY: format
format:
	@poetry run ruff format .
	@poetry run ruff check --fix .
	@poetry run docformatter --in-place --recursive .

build:
	@docker-compose build cumplo-herald --build-arg CUMPLO_PYPI_BASE64_KEY=`base64 -i cumplo-pypi-credentials.json`

start:
	@docker-compose up -d cumplo-herald

down:
	@docker-compose down

.PHONY: login
login:
	@gcloud config configurations activate $(PROJECT_ID)
	@gcloud auth application-default login

.PHONY: update-common
update-common:
	@rm -rf .venv
	@poetry cache clear --no-interaction --all cumplo-pypi
	@poetry update
