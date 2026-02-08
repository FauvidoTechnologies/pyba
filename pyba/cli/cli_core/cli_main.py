from typing import Optional

from pyba import Engine
from pyba.cli.cli_core.arg_parser import ArgParser
from pyba.core.lib import DFS, BFS, Step
from pyba.database import Database


class CLIMain(ArgParser):
    """
    Main class for pyba CLI
    """

    def __init__(self):
        super().__init__()

        self.database = self.initialise_database()
        self.initialise_engine()

        self.generate_code = self.arguments.generate_code
        self.code_output_path = self.arguments.code_output_path

        self.mode = self.arguments.operation_mode

    def initialise_database(self) -> Optional[Database]:
        """
        Helper function to generate and initialise the database
        """
        database = None
        if self.arguments.mode == "database":
            database_configs = {
                "engine": self.arguments.database_engine,
                "name": self.arguments.database_name,
                "username": self.arguments.database_username or None,
                "password": self.arguments.database_password or None,
                "host": self.arguments.database_host or None,
                "port": self.arguments.database_port or None,
                "ssl_mode": self.arguments.postgres_ssl_mode,
            }

            database = Database(**database_configs)

        return database

    def initialise_engine(self):
        """
        Initialises the engine using the provided user parameters
        """

        self.task = self.arguments.task
        self.automated_login_sites = self.arguments.automated_login_sites

        engine_configs = {
            "openai_api_key": self.arguments.openai_api_key,
            "vertexai_project_id": self.arguments.vertexai_project_id,
            "vertexai_server_location": self.arguments.vertexai_server_location,
            "gemini_api_key": self.arguments.gemini_api_key,
            "headless": self.arguments.headless_mode,
            "handle_dependencies": self.arguments.handle_dependencies,
            "use_random": self.arguments.use_random,
            "use_logger": self.arguments.use_logger,
            "enable_tracing": self.arguments.enable_tracing,
            "trace_save_directory": self.arguments.trace_save_directory,
            "database": self.database,
        }

        if self.arguments.operation_mode in {"DFS", "BFS"}:
            engine_configs["max_depth"] = self.arguments.max_depth
            engine_configs["max_breadth"] = self.arguments.max_breadth

        if self.arguments.operation_mode == "BFS":
            self.engine = BFS(**engine_configs)
        elif self.arguments.operation_mode == "DFS":
            self.engine = DFS(**engine_configs)
        elif self.arguments.operation_mode == "STEP":
            self.engine = Step(**engine_configs)
        else:
            self.engine = Engine(**engine_configs)

    def cli_sync_run(self):
        """
        The CLI run function which calls the main runner with the instantiated arguments
        """
        if self.mode == "STEP":
            self.engine.sync_start(automated_login_sites=self.automated_login_sites)
            try:
                while True:
                    instruction = input(">> ").strip()
                    if not instruction:
                        continue
                    if instruction == "quit":
                        break
                    output = self.engine.sync_step(instruction)
                    if output:
                        print(f"[output] {output}")
            finally:
                self.engine.sync_stop()
        else:
            self.engine.sync_run(self.task, automated_login_sites=self.automated_login_sites)

        if self.generate_code:
            self.engine.generate_code(output_path=self.code_output_path)

    def cli_async_run(self):
        """
        The CLI run function for Async endpoints
        """
        self.engine.run(self.task, automated_login_sites=self.automated_login_sites)
