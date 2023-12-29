import sqlite3
import config
import file
import logger

connection = sqlite3.connect(config.DATABASE_FILEPATH)


def execute(sql):
    try:
        with connection:
            return connection.execute(sql)
    except Exception as e:
        logger.error('SQL statement failed to execute!', exc_info=e)


def create_tables():
    try:
        connection.executescript(file.read(config.CREATE_TABLES_SCRIPT))
    except Exception as e:
        logger.error('SQL table creation failed.', exc_info=e)


def drop_tables():
    try:
        connection.executescript(file.read(config.DROP_TABLES_SCRIPT))
    except Exception as e:
        logger.error('SQL table dropping failed.', exc_info=e)