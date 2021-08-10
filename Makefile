.EXPORT_ALL_VARIABLES:
BETTER_EXCEPTIONS=1
DJANGO_SETTINGS_MODULE?=backend.settings.lint

migrate:
	python src/manage.py migrate

migrations:
	python src/manage.py makemigrations

test: migrate
	pytest --testmon src || \
	if [ $$? = 5 ]; \
	  then exit 0; \
	  else exit $$?; \
	fi

coverage: migrate
	pytest --cov=. --cov-report=xml src && \
	coverage html && \
	which xdg-open && \
	xdg-open htmlcov/index.html || true

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

fake-data:
	python -m scripts.fake generate $(ARGS)

fake-bulk-data:
	python -m scripts.fake generate --teams 10000 --users 2 --categories 10 --challenges 100 --solves 1000000

clean-db:
	python scripts/clean_db.py

clean-test:
	rm -rf /tmp/ractf-linting.cache /tmp/ractf-linting.db .testmondata

clean-dev-server:
	docker-compose rm -sf
