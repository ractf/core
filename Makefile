.EXPORT_ALL_VARIABLES:
BETTER_EXCEPTIONS=1
PYTHONPATH=$(shell pwd)/src
DJANGO_SETTINGS_MODULE?=core.settings.lint

migrate:
	python src/manage.py migrate

test: migrate
	pytest --testmon || \
	if [ $$? = 5 ]; \
	  then exit 0; \
	  else exit $$?; \
	fi

coverage: migrate
	pytest --cov=. --cov-report=xml && \
	coverage html && \
	[ "$$CI" != "true" ] && \
	xdg-open htmlcov/index.html || true

format:
	isort src && \
	black src

lint: migrate
	flakehell lint src && \
	isort --check-only src

dev-server:
	docker-compose build && \
	docker-compose up -d

dev-server-attach:
	docker-compose build && \
	docker-compose up

dev-test: dev-server
	docker-compose exec backend pytest --cov=src src

dev-server-logs: dev-server
	docker-compose logs -f

dev-server-down:
	docker-compose down

fake-data:
	python -m scripts/fake generate $(ARGS)

fake-bulk-data:
	python -m scripts.fake generate --teams 10000 --users 2 --categories 10 --challenges 100 --solves 1000000

clean-db:
	python scripts/clean_db.py

clean-test:
	rm -rf /tmp/ractf-linting.cache /tmp/ractf-linting.db .testmondata
