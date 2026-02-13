import sys
from argparse import ArgumentParser

from pyba.version import version


class ArgParser(ArgumentParser):
    """
    Argparser class. This class holds the definitions for each flag
    along with their default values and parses them individually
    """

    def __init__(self) -> None:
        super().__init__(prog="pyba", add_help=True)

        self.add_arguments()
        self.initialise_arguments()

    def add_arguments(self):
        main_options = self.add_argument_group(
            "Main", "The main input options. (as in the 'main' file)"
        )
        main_options.add_argument(
            "-V",
            "--version",
            action="store_true",
            dest="show_version",
            default=False,  # Do not hardcode this, read from a version file
            help="Display the software version",
        )

        base_parser = ArgumentParser(add_help=False)
        base_parser.add_argument(
            "--openai-api-key",
            action="store",
            default=None,
            dest="openai_api_key",
            help="OpenAI API Key if you wish to run the automations using OpenAI's models",
        )

        base_parser.add_argument(
            "--vertexai-project-id",
            action="store",
            default=None,
            dest="vertexai_project_id",
            help="VertexAI project ID if you wish to run the automations using VertexAI's gemini models. Note that vertexai must be properly setup before using this option",
        )

        base_parser.add_argument(
            "--vertexai-server-location",
            action="store",
            default=None,
            dest="vertexai_server_location",
            help="VertexAI server location if you wish to run the automations using VertexAI's gemini models. Note that vertexai must be properly setup before using this option",
        )

        base_parser.add_argument(
            "--gemini-api-key",
            action="store",
            default=None,
            dest="gemini_api_key",
            help="Gemini API key if you wish to run the automations using Gemini-2.5-pro without using VertexAI",
        )

        base_parser.add_argument(
            "--model-name",
            action="store",
            default=None,
            dest="model_name",
            help="Override the default model for the chosen provider",
        )

        base_parser.add_argument(
            "--headless",
            action="store_true",
            default=False,
            dest="headless_mode",
            help="Run the automations in headless mode. Useful for web scraping",
        )

        base_parser.add_argument(
            "--handle-deps",
            action="store_true",
            default=False,
            dest="handle_dependencies",
            help="Automatically handle all playwright dependencies",
        )

        base_parser.add_argument(
            "-v",
            action="store_true",
            default=False,
            dest="use_logger",
            help="Start the automations in the verbose mode to get live updates",
        )

        base_parser.add_argument(
            "-r",
            action="store_true",
            default=False,
            dest="use_random",
            help="Use random mouse and scroll movements in between timeouts and waits",
        )

        base_parser.add_argument(
            "--enable-tracing",
            action="store_true",
            default=False,
            dest="enable_tracing",
            help="Start's tracing all playwright moves and network requests to create a zip file which can be viewed in playwright traceviewer",
        )

        base_parser.add_argument(
            "--trace-save-dir",
            action="store",
            default=None,
            dest="trace_save_directory",
            help="Directory to save the trace zip file",
        )

        base_parser.add_argument(
            "-t",
            "--task",
            action="store",
            dest="task",
            default=None,
            help="The task which needs to be automated as a string",
        )

        base_parser.add_argument(
            "-L",
            "--login-sites",
            action="append",
            dest="automated_login_sites",
            default=None,
            help="The automated login engine names. Note: To use these you will need to set the username and password in your enviornment. Please read the man page.",
        )

        base_parser.add_argument(
            "--op-mode",
            action="store",
            dest="operation_mode",
            default="Normal",
            help="Select the operation mode from (DFS|BFS|STEP|Normal), defaults at Normal mode",
        )

        base_parser.add_argument(
            "--max-depth",
            action="store",
            dest="max_depth",
            default=5,
            help="Define the maximum depth to go into for exploratory scans",
        )

        base_parser.add_argument(
            "--max-breadth",
            action="store",
            dest="max_breadth",
            default=5,
            help="Define the maximum number of different ideas to explore in the exploratory mode",
        )

        base_parser.add_argument(
            "--low-memory-usage",
            action="store",
            dest="low_memory_usage",
            default=False,
            help="Determines whether to enable the low memory kwargs in playwright browser initiation",
        )

        subparsers = self.add_subparsers(
            title="modes",
            dest="mode",
            required=False,  # Run the base and main flags without setting the mode
            description="Choose the database mode if you wish to log actions and use them for script generation",
            parser_class=ArgumentParser,
        )

        # TODO
        # clarification_mode = subparsers.add_parser("clarify", help="Clarification mode for asking questions to the user about unsure steps", parents=[base_parser])

        # Normal Mode
        subparsers.add_parser(
            "normal",
            help="Does not store logs or ask clarifications during automation",
            parents=[base_parser],
        )

        # Database Mode
        database_mode = subparsers.add_parser(
            "database",
            help="Store logs in the database for script creation",
            parents=[base_parser],
        )
        database_mode.add_argument(
            "-e",
            "--engine",
            action="store",
            default=None,
            required=True,
            dest="database_engine",
            help="The database engine you wish to use",  # This needs to be more explicit
        )

        database_mode.add_argument(
            "-n",
            "--name",
            action="store",
            default=None,
            required=True,
            dest="database_name",
            help="Name of the database in case of MySQL and PostgreSQL, and the path to the database file in case of SQLite",
        )

        database_mode.add_argument(
            "-u",
            "--username",
            action="store",
            default=None,
            dest="database_username",
            help="The username for logging into the database server while using MySQL or PostgreSQL",
        )
        database_mode.add_argument(
            "-p",
            "--password",
            action="store",
            default=None,
            dest="database_password",
            help="The password for logging into the database server while using MySQL or PostgreSQL",
        )
        database_mode.add_argument(
            "-H",
            "--host-name",
            action="store",
            default=None,
            dest="database_host",
            help="The host IP serving the MySQL or PostgreSQL databases",
        )
        database_mode.add_argument(
            "-P",
            "--port",
            action="store",
            default=None,
            dest="database_port",
            help="The host port serving the MySQL or PostgreSQL databases",
        )
        database_mode.add_argument(
            "--ssl-mode",
            action="store",
            default="disabled",
            dest="postgres_ssl_mode",
            help="The ssl_mode for running PostgreSQL databases. Can be disable or required, defaults at disabled",
        )
        database_mode.add_argument(
            "--generate-code",
            action="store_true",
            default=False,
            dest="generate_code",
            help="Use the stored actions to generate an automation script",
        )
        database_mode.add_argument(
            "--code-output-path",
            action="store",
            default=None,
            dest="code_output_path",
            help="The file destination for the output path of the generated code. Defaults at `/tmp/script.py`",
        )

    def initialise_arguments(self):
        """
        check all rules and requirements for ARGS

        Args:
        api_forms: values from nettacker.api

        Returns:
        all ARGS with applied rules
        """
        options = self.parse_args()

        if options.show_version:
            print(f"Software version: {version}")
            sys.exit(0)

        if options.automated_login_sites:
            for site in options.automated_login_sites:
                print(f"Automated login enabled for: {site}")

        if options.operation_mode:
            if options.operation_mode not in {"DFS", "BFS", "Normal", "STEP"}:
                print(
                    f"Mode of operation '{options.operation_mode}' not recognized! Please choose from (BFS|DFS|STEP|Normal)"
                )
                sys.exit(0)

        # passing all the keys directly to the run function because that handles it using the provider instance
        if options.mode == "database":
            if options.database_engine not in ["sqlite", "mysql", "postgres"]:
                print("Wrong database engine chosen. Please choose from sqlite, mysql or postgres")
                sys.exit(0)

            if not options.code_output_path:
                # Default save to /tmp/pyba_script.py
                options.code_output_path = "/tmp/pyba_script.py"
                print(
                    "Output path not specified, the generated script will be saved at /tmp/pyba_script.py"
                )

        self.arguments = options
