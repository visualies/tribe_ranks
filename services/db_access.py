import mysql.connector
from mysql.connector import Error
from mysql.connector.connection import MySQLConnection
from mysql.connector import pooling
from services import file_manager


def open_connection_pool():
    config = file_manager.load_config()
    try:
        connection_pool = mysql.connector.pooling.MySQLConnectionPool(pool_name="pool_party",
                                                                      pool_size=4,
                                                                      pool_reset_session=True,
                                                                      host=config["database"]["host"],
                                                                      database=config["database"]["database"],
                                                                      user=config["database"]["user"],
                                                                      password=config["database"]["password"])

        # Get connection object from a pool
        db = connection_pool.get_connection()

        if db.is_connected():
            db_info = db.get_server_info()
            print(f"Connected to MySQL database using connection pool [MySQL server version: {db_info}]")

            context = db.cursor()
            context.execute("select database();")
            record = context.fetchone()
            print(f"Connected to {record[0]}")

    except Error as e:
        print("Error while connecting to MySQL using Connection pool ", e)
    finally:
        # closing database connection.
        if db.is_connected():
            context.close()
            db.close()
            return connection_pool


# startup connection pooling
pool = open_connection_pool()


# get connection from pool
def get_connection():
    try:
        connection = pool.get_connection()
    except Error as e:
        print("Error while connecting to MySQL using Connection pool", e)
        return
    finally:
        return connection


def check_tables():
    config = file_manager.load_config()

    connection = get_connection()
    context = connection.cursor()

    context.execute(f"SELECT * FROM INFORMATION_SCHEMA.TABLES WHERE TABLE_NAME = 'tribes'")
    record = context.fetchone()
    if record is None:
        context.execute(f"CREATE TABLE `{config['database']['database']}`.`tribes` ( `id` INT NOT NULL AUTO_INCREMENT , `steam_id` BIGINT(17) UNSIGNED NOT NULL , `tribe_name` VARCHAR(200) NOT NULL , `tribe_size` INT(8) NOT NULL , `map_name` VARCHAR(200) NOT NULL , `last_seen` DATETIME NOT NULL , PRIMARY KEY (`id`)) ENGINE = InnoDB;")


check_tables()
