.EXPORT_ALL_VARIABLES:

BETTER_EXCEPTIONS=1
DJANGO_SETTINGS_MODULE=backend.settings.lint

migrate:
	python src/manage.py migrate

test: migrate
	pytest --testmon src || \
	if [ $$? = 5 ]; \
	  then exit 0; \
	  else exit $$?; \
	fi

coverage: migrate
	pytest --cov=src --cov-report=xml src && \
	coverage html && \
	xdg-open htmlcov/index.html

format:
	isort src && \
	black src

lint:
	flake8 && \
	isort --check-only src

dev-server:
	docker-compose build && \
	docker-compose up -d

dev-test: dev-server
	docker-compose exec backend pytest --cov=src src
