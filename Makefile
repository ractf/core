test:
	export DJANGO_SETTINGS_MODULE='backend.settings.lint' && \
	cd src && \
	BETTER_EXCEPTIONS=1 \
	python manage.py migrate && \
	pytest --cov=. --cov-report=xml

format:
	isort -rc src && \
	black src

lint:
	flake8 && \
	isort --check-only src
