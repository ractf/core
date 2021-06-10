import os

import psycopg2

name = os.getenv("SQL_DATABASE")
user = os.getenv("SQL_USER")
password = os.getenv("SQL_PASSWORD")
host = os.getenv("SQL_HOST")
port = os.getenv("SQL_PORT")

try:
    connection = psycopg2.connect(user=user, password=password, host=host, port=port, database="template1")
    connection.set_isolation_level(0)
    with connection.cursor() as cursor:
        cursor.execute(f"DROP DATABASE {name}")
        cursor.execute(f"CREATE DATABASE {name}")
finally:
    if "conn" in vars():
        connection.close()
