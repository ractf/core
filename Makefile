migrate:
	export DJANGO_SETTINGS_MODULE='backend.settings.lint' && \
	export BETTER_EXCEPTIONS=1 && \
	python src/manage.py migrate

test: migrate
	pytest --testmon || \
	if [ $$? = 5 ]; \
	  then exit 0; \
	  else exit $$?; \
	fi

coverage: migrate
	pytest --cov=src --cov-report=xml && \
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
