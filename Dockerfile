FROM docker.io/library/python:3.12-slim

ARG BUILD_DEPS="build-essential"

WORKDIR /app/

ENV PYTHONUNBUFFERED=1 \
  PIP_NO_CACHE_DIR=off \
  PYTHONPYCACHEPREFIX=/tmp \
  PATH=/root/.local/bin:/app/src/manage.py${PATH}

RUN set -ex \
  && apt-get update && apt-get -y --no-install-recommends install $BUILD_DEPS libpq-dev netcat-traditional make git curl \
  && rm -rf /var/lib/apt/lists/* \
  && curl -sSL https://install.python-poetry.org | python3 - \
  && poetry config virtualenvs.create false

COPY poetry.lock pyproject.toml /app/

RUN poetry install --no-root --no-interaction \
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false $BUILD_DEPS

COPY . /app/

EXPOSE 8000
