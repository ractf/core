#! /bin/sh


echo -n "Waiting for postgres... "
while ! nc -z $SQL_HOST $SQL_PORT; do
    sleep 0.69
done
echo "Done."


echo "Running migrations... "
/app/src/manage.py migrate
echo "Done."

if [[ "$LOAD_FIXTURES" ]]
then
  /app/src/manage.py flush
  /app/src/manage.py loaddata test_fixtures
fi

exec "$@"
