import psycopg2
from psycopg2 import OperationalError

from core.settings.environments import (RESOURCE, DB_NAME, DB_PASSWORD,
                                        DB_USERNAME)

try:
    conn = psycopg2.connect(
        dbname='postgres',  # Connect to the default database
        user=DB_USERNAME,
        password=DB_PASSWORD,
        host=RESOURCE,
        port=5432)
    print("Database server is up!")

    conn.autocommit = True  # Enable autocommit to execute CREATE DATABASE
    with conn.cursor() as cursor:
        cursor.execute(
            f"SELECT 1 FROM pg_database WHERE datname = '{DB_NAME}'")
        exists = cursor.fetchone()
        if not exists:
            print(f"Database '{DB_NAME}' does not exist. Creating...")
            cursor.execute(
                f"CREATE DATABASE {DB_NAME} WITH OWNER {DB_USERNAME}")
            print(f"Database '{DB_NAME}' created!")
        else:
            print(f"Database '{DB_NAME}' already exists.")
except OperationalError:
    print("Database server not ready, please check db status.")
    raise Exception('DB  NOT AVAILABLE.')
finally:
    if conn:
        conn.close()
