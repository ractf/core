#! /bin/sh


echo -n "Waiting for postgres... "
while ! nc -z $SQL_HOST $SQL_PORT; do
    sleep 0.69
done
echo "Done."


echo -n "Waiting for django... "
while ! nc -z web 8000; do
    sleep 0.69
done
echo "Done."


if [ -f /etc/newrelic.ini ]
then
  NEW_RELIC_CONFIG_FILE=/etc/newrelic.ini newrelic-admin run-program "$@"
else
  exec "$@"
fi
