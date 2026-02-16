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
    Client-side database interface that minimizes config usage.
    """

    def __init__(
        self,
        engine: Literal["sqlite", "postgres", "mysql"],
        name: str = None,
        host: str = None,
        port: int = None,
        username: str = None,
        password: str = None,
        ssl_mode: Literal["disable", "require"] = None,
    ):
        """
        Initialize database connection.

        Args:
            engine: Database engine type ("sqlite", "postgres", or "mysql").
                   Can also be specified in config if not provided here.
            name: Database name or file path (for SQLite).
            host: Database server host.
            port: Database server port.
            username: Database username.
            password: Database password.
            ssl_mode: SSL mode for PostgreSQL ("disable" or "require").

        SQLite configuration:
            - engine: "sqlite"
            - name: Path to the database file
            - Other parameters can be left empty

        MySQL configuration:
            - engine: "mysql"
            - name: Name of the MySQL database
            - username, password: Credentials for server authentication
            - host, port: Server location (default port: 3306)

        PostgreSQL configuration:
            - engine: "postgres"
            - name: Name of the PostgreSQL database
            - username, password: Credentials for server authentication
            - host, port: Server location (default port: 5432)
            - ssl_mode: "require" for encrypted databases
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
        Builds connection URLs for different database engines for SQLAlchemy usage.

        Args:
            engine_name: The database engine name for initialization.

        Returns:
            Connection string for SQLAlchemy.
        """

        return {
            "postgres": f"postgresql+psycopg2://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}?sslmode={self.ssl_mode}",
            "mysql": f"mysql+pymysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.name}",
            "sqlite": f"sqlite:///{self.name}",
        }[engine_name]

    def create_connection(self, engine_name: Literal["sqlite", "postgres", "mysql"]):
        """
        Creates a connection to the database.

        Args:
            engine_name: The database engine name.

        Returns:
            Database session if successful, otherwise False.
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
            self.log.error(f"Couldn't create a connection to the database: {e}")
            return False

    def initialise_tables_and_database(self):
        """
        Manages the creation of database and tables for SQLite, PostgreSQL, and MySQL.
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
