test:
	export DJANGO_SETTINGS_MODULE='backend.settings.lint' && \
	cd src && \
	BETTER_EXCEPTIONS=1 \
	python manage.py migrate && \
	pytest --testmon || \
	if [ $$? = 5 ]; \
	  then exit 0; \
	  else exit $$?; \
	fi

coverage:
	export DJANGO_SETTINGS_MODULE='backend.settings.lint' && \
	cd src && \
	BETTER_EXCEPTIONS=1 \
	python manage.py migrate && \
	pytest --cov=. --cov-report=xml && \
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
