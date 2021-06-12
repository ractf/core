"""Script for clearing the connected database of all data."""

import os
from os import getenv

import psycopg2


with psycopg2.connect(
    user=getenv("SQL_USER"),
    password=getenv("SQL_PASSWORD"),
    host=getenv("SQL_HOST"),
    port=getenv("SQL_PORT"),
    database="template1",
) as connection:
    connection.set_isolation_level(0)
    with connection.cursor() as cursor:
        cursor.execute(f"DROP DATABASE {os.getenv('SQL_DATABASE')}")
        cursor.execute(f"CREATE DATABASE {os.getenv('SQL_DATABASE')}")
