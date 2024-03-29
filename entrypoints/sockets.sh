#!/usr/bin/env sh

echo "Waiting for postgres... "
while ! nc -z $SQL_HOST $SQL_PORT
do
  sleep 0.69
done
echo "Done."

echo "Waiting for django... "
while ! nc -z backend 8000
do
  sleep 0.69
done
echo "Done."

export GUNICORN_CMD_ARGS="--chdir=/app/src/ --reload --workers=4 --bind=0.0.0.0:8000 --worker-class=uvicorn.workers.UvicornWorker"
if [ -f /etc/newrelic.ini ]
then
  NEW_RELIC_CONFIG_FILE=/etc/newrelic.ini newrelic-admin run-program "$@"
else
  exec $@
fi
