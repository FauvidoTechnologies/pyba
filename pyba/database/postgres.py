from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError

from pyba.database.models import Base


class PostgresHandler:
    """
    Class handling Postgres database creation
    """

    def __init__(self, database_engine_configs):
        """
        Args:
            database_engine_configs: User-supplied configurations imported from the Database class.
        """

        self.database_engine_configs = database_engine_configs
        self.database_connection_string = self.database_engine_configs.database_connection_string

        self.engine = create_engine(self.database_connection_string)

    def create_postgres_database(self):
        """
        Creates a PostgreSQL database.

        If the database does not exist, connects to the default postgres database
        using the connection string "postgresql+psycopg2://{username}:{password}@{host}:{port}/postgres"
        and creates a new database from there.
        """
        try:
            Base.metadata.create_all(self.engine)
        except OperationalError:
            local_engine = create_engine(
                f"postgresql+psycopg2://{self.database_engine_configs.username}:{self.database_engine_configs.password}@{self.database_engine_configs.host}:{self.database_engine_configs.port}/postgres"
            )
            conn = local_engine.connect()
            conn = conn.execution_options(isolation_level="AUTOCOMMIT")

            conn.execute(text(f"CREATE DATABASE {self.database_engine_configs.name}"))
            conn.close()

            Base.metadata.create_all(self.engine)

    def setup(self):
        """
        Entrypoint for database and table creation
        """
        self.create_postgres_database()
