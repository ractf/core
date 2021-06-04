#! /bin/sh


if [ -z "$prometheus_multiproc_dir" ]
then
  echo "No Prometheus directory set."
else
  echo "Deleting the contents of ${prometheus_multiproc_dir}"
  rm $prometheus_multiproc_dir/* -rf
fi

stdbuf -o 0 echo -n "Waiting for postgres... "
while ! nc -z $SQL_HOST $SQL_PORT
do
  sleep 0.69
done
echo "Done."


echo "Running migrations..."
/app/src/manage.py migrate
echo "Done."


if [ "$LOAD_FIXTURES" ]
then
  /app/src/manage.py flush --no-input
  /app/src/manage.py loaddata test_fixtures
fi


if [ -f /etc/newrelic.ini ]
then
  NEW_RELIC_CONFIG_FILE=/etc/newrelic.ini newrelic-admin run-program "$@"
else
  exec "$@"
fi
