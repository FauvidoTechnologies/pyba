from sqlalchemy import create_engine, text

from pyba.database.models import Base


class MySQLHandler:
    """
    Class to manage MySQL database and table dependencies
    """

    def __init__(self, database_engine_configs):
        """
        Args:
            database_engine_configs: User-supplied configurations imported from the Database class.
        """
        self.database_engine_configs = database_engine_configs
        self.database_connection_string = self.database_engine_configs.database_connection_string

        self.engine = create_engine(self.database_connection_string)

    def mysql_create_database(self):
        """
        Method to create a MySQL database using the specified credentials
        """

        try:
            with self.engine.connect() as conn:
                existing_databases = conn.execute(text("SHOW DATABASES;"))
                existing_databases = [d[0] for d in existing_databases]

                if self.database_engine_configs.name not in existing_databases:
                    conn.execute(
                        text("CREATE DATABASE {0} ".format(self.database_engine_configs.name))
                    )
        except Exception:
            pass

    def mysql_create_tables(self):
        """
        Creates the MySQL tables.
        """
        Base.metadata.create_all(self.engine)

    def setup(self):
        """
        Entrypoint for database and table creation
        """
        self.mysql_create_database()
        self.mysql_create_tables()
