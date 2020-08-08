FROM python:3.8-slim

ARG BUILD_DEPS="build-essential curl"

RUN set -ex \
  && apt-get update && apt-get -y --no-install-recommends install $BUILD_DEPS libpq-dev netcat git \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false $BUILD_DEPS \
  && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=off

WORKDIR /app/

COPY poetry.lock pyproject.toml /app/

RUN set -ex && apt-get update && apt-get -y --no-install-recommends install $BUILD_DEPS

RUN curl -sSL "https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py" | POETRY_PREVIEW=1 python \
  && . $HOME/.poetry/env \
  && poetry config virtualenvs.create false \
  && poetry install $(test "$BUILD_ENV" = production && echo "--no-dev") --no-root --no-interaction --no-ansi

RUN apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false $BUILD_DEPS \
  && rm -rf /var/lib/apt/lists/*

ENV PATH=/root/.poetry/bin:${PATH}
COPY . /app/

WORKDIR /app/src

ENV PATH=/root/.poetry/bin:/app/src/manage.py${PATH}

EXPOSE 8000
