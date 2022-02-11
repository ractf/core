FROM docker.io/library/python:3.9-slim

ARG BUILD_DEPS="build-essential"

RUN set -ex \
  && apt-get update && apt-get -y --no-install-recommends install $BUILD_DEPS libpq-dev make git curl \
  && rm -rf /var/lib/apt/lists/* \
  && curl -sSL "https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py" | python \
  && . $HOME/.poetry/env \
  && poetry config virtualenvs.create false

COPY poetry.lock pyproject.toml /app/
WORKDIR /app/

ENV PYTHONUNBUFFERED=1 \
  PIP_NO_CACHE_DIR=off \
  PYTHONPYCACHEPREFIX=/tmp \
  PATH=/root/.poetry/bin:/app/src/manage.py${PATH}

RUN poetry install --no-root --no-interaction \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false $BUILD_DEPS

COPY . /app/

EXPOSE 8000
