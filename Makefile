test:
	export DJANGO_SETTINGS_MODULE='backend.settings.lint' && \
	cd src && \
	BETTER_EXCEPTIONS=1 \
	python manage.py migrate && \
	pytest --testmon --cov=. --cov-report=xml --cov-fail-under=80

format:
	isort -rc src && \
	black src

lint:
	flake8 && \
	isort --check-only src
