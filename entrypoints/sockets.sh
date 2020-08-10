#! /bin/sh


echo -n "Waiting for postgres... "
while ! nc -z $SQL_HOST $SQL_PORT; do
    sleep 0.69
done
echo "Done."


echo -n "Waiting for django... "
while ! nc -z backend 8000; do
    sleep 0.69
done
echo "Done."


exec "$@"
