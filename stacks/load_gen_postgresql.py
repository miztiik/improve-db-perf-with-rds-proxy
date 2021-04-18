import psycopg2
from psycopg2 import Error

import json
import logging
import datetime
import os
import random
import uuid


class GlobalArgs:
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    S3_BKT_NAME = os.getenv("STORE_EVENTS_BKT")
    DB_ENDPOINT = "ss1c7pkr2igrogf.ca64q8ficuhu.us-east-1.rds.amazonaws.com"
    DB_PORT = "5432"
    DB_NAME = "store_events"
    DB_USER_NAME = "mystiquemaster"
    DB_PASSWORD = "15UReFwGb7YO1Oe3"
    S3_PREFIX = "store_events"


def set_logging(lv=GlobalArgs.LOG_LEVEL):
    logging.basicConfig(level=lv)
    logger = logging.getLogger()
    logger.setLevel(lv)
    return logger


logger = set_logging()


def _rand_coin_flip():
    r = False
    if os.getenv("TRIGGER_RANDOM_FAILURES", True):
        if random.randint(1, 100) > 90:
            r = True
    return r


def _gen_uuid():
    return str(uuid.uuid4())


def put_object(_pre, data):
    try:
        _r = _s3.put_object(
            Bucket=GlobalArgs.S3_BKT_NAME,
            Key=f"event_type={_pre}/dt={datetime.datetime.now().strftime('%Y_%m_%d')}/{datetime.datetime.now().strftime('%s%f')}.json",
            Body=json.dumps(data).encode("UTF-8"),
        )
        logger.debug(f"resp: {json.dumps(_r)}")
    except Exception as e:
        logger.exception(f"ERROR:{str(e)}")


events_table="""
CREATE TABLE IF NOT EXISTS sales(
    id SERIAL PRIMARY KEY,
    sku_id INTEGER
    );
"""

"""
psql \
   --host="ss1c7pkr2igrogf.ca64q8ficuhu.us-east-1.rds.amazonaws.com" \
   --port=5432 \
   --username=mystiquemaster \
   --password \
   --dbname=store_events 
"""

INSERT INTO sales(id, sku_id) VALUES(1, 34);

def lambda_handler(event, context):

    try:
        # Connect to an existing database
        connection = psycopg2.connect(
            user=GlobalArgs.DB_USER_NAME,
            password=GlobalArgs.DB_PASSWORD,
            host=GlobalArgs.DB_ENDPOINT,
            port=GlobalArgs.DB_PORT,
            database=GlobalArgs.DB_NAME
        )

        conn = psycopg2.connect(
            host=GlobalArgs.DB_ENDPOINT,
            database=GlobalArgs.DB_NAME,
            user=GlobalArgs.DB_USER_NAME,
            password=GlobalArgs.DB_PASSWORD
        )

        # Create a cursor to perform database operations
        cursor = connection.cursor()
        # Print PostgreSQL details
        print("PostgreSQL server information")
        # print(connection.get_dsn_parameters(), "\n")
        # Executing a SQL query
        cursor.execute("SELECT version();")
        # Fetch result
        record = cursor.fetchone()
        print("You are connected to - ", record, "\n")

    except (Exception, Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        if (connection):
            cursor.close()
            connection.close()
            print("PostgreSQL connection is closed")

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "all_good"
        })
    }


lambda_handler({}, {})
