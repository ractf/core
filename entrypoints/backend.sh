#!/usr/bin/env sh

if [ -z "$prometheus_multiproc_dir" ]
then
  echo "No Prometheus directory set."
else
  echo "Deleting the contents of ${prometheus_multiproc_dir}"
  rm $prometheus_multiproc_dir/* -rf
fi

echo "Running migrations..."
/app/src/manage.py migrate
echo "Done."

export GUNICORN_CMD_ARGS="--chdir=/app/src/ --reload --workers=4 --bind=0.0.0.0:8000 --worker-class=gthread"
if [ -f /etc/newrelic.ini ]
then
  NEW_RELIC_CONFIG_FILE=/etc/newrelic.ini newrelic-admin run-program "$@"
else
  exec $@
fi
