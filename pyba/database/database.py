from typing import Literal

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import pyba.core.helpers as global_vars
from pyba.database.mysql import MySQLHandler
from pyba.database.postgres import PostgresHandler
from pyba.database.sqlite import SQLiteHandler
from pyba.logger import get_logger
from pyba.utils.load_yaml import load_config

config = load_config("general")["database"]


class Database:
    """
    Client-side database function -> Minimizes the config use
    """

    def __init__(
        self,
        engine: Literal[
            "sqlite", "postgres", "mysql"
        ],  # Optional: Can be specified inside the config as well
        name: str = None,
        host: str = None,
        port: int = None,
        username: str = None,
        password: str = None,
        ssl_mode: Literal["disable", "require"] = None,
    ):
        """
        Args:
                sqlite:
                        `engine`: "sqlite"
                        `name`: path to the database file
                        other details can be left empty

                mysql:
                        `engine`: "mysql"
                        `name`: Name of the mysql database
                        `username` and `password`: For logging into the server
                        `host` and `port`: Location of the server

                        Note: Default port is 3306 for MySQL

                postgres:
                        `engine`: "postgres"
                        `name`: Name of the postgres database
                        `username` and `password`: For logging into the server
                        `host` and `port`: Location of the server

                        Note: Default port is 5432 for MySQL
                        Note: `ssl_mode`: "require" for encrypted databases

        Optionally supports entries defined inside the config as well in case they are not provided here.

        > This engine is the recommended way to define the database structure
        """
        self.engine: str = engine or config["engine"]
        self.log = get_logger()

        self.name: str = name or config["name"]
        self.host: str = host or config["host"]
        self.port: int = port or config["port"]
        self.username: str = username or config["username"]
        self.password: str = password or config["password"]
        self.ssl_mode: str = ssl_mode or config["ssl_mode"]

        self.database_connection_string = self.build_connection_string(engine_name=self.engine)
        self.session = self.create_connection(engine_name=self.engine)

        self.initialise_tables_and_database()

    def build_connection_string(self, engine_name: Literal["sqlite", "postgres", "mysql"]) -> str:
        """
        Defines connection URLs for the different databases for SQLAlchemy usage

        Args:
                `engine_name`: The database model name for initialisation

        Returns:
                A string for SQLAlchemy connection
        """

        return {
            "postgres": f"postgresql+psycopg2://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}?sslmode={self.ssl_mode}",
            "mysql": f"mysql+pymysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}",
            "sqlite": f"sqlite:///{self.name}",
        }[engine_name]

    def create_connection(self, engine_name: Literal["sqlite", "postgres", "mysql"]):
        """
        Function to create connections to the database

        Args:
                `engine_name`: The database engine name

        Returns:
                connection if successful otherwise False
        """
        connection_args = {}

        if engine_name == "sqlite":
            connection_args["check_same_thread"] = False

        pool_kwargs = (
            {"pool_size": 5, "max_overflow": 5} if global_vars._low_memory else {"pool_size": 50}
        )

        try:
            db_engine = create_engine(
                self.database_connection_string,
                connect_args=connection_args,
                pool_pre_ping=True,
                **pool_kwargs,
            )

            Session = sessionmaker(bind=db_engine)

            return Session()
        except Exception as e:
            # We might get an OperationalError here if the DB doesn't exist yet
            self.log.error(f"Couldn't create a connection to the database: {e}")
            return False

    def initialise_tables_and_database(self):
        """
        Method to manage the creation of sqlite, postgres and mysql database and tables
        """
        handler_map = {
            "sqlite": SQLiteHandler,
            "postgres": PostgresHandler,
            "mysql": MySQLHandler,
        }

        HandlerClass = handler_map.get(self.engine)
        handler = HandlerClass(database_engine_configs=self)
        handler.setup()
        self.log.success(f"Database setup for {self.engine} complete.")
