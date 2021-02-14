#! /bin/sh


stdbuf -o 0 echo -n "Waiting for postgres... "
while ! nc -z $SQL_HOST $SQL_PORT
do
  sleep 0.69
done
echo "Done."


if [[ -z "${SKIP_DJANGO_CHECK}" ]]; then
  echo "Skipping Django check"
else
  stdbuf -o 0 echo -n "Waiting for django... "
  while ! nc -z backend 8000
  do
    sleep 0.69
  done
  echo "Done."
fi



if [ -f /etc/newrelic.ini ]
then
  NEW_RELIC_CONFIG_FILE=/etc/newrelic.ini newrelic-admin run-program "$@"
else
  exec "$@"
fi
