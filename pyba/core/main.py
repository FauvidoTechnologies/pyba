import asyncio
import uuid
from typing import List, Union

from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from pydantic import BaseModel

from pyba.core.lib.action import perform_action
from pyba.core.lib.mode.base import BaseEngine
from pyba.core.scripts import LoginEngine
from pyba.database import Database
from pyba.utils.common import initial_page_setup, serialize_action
from pyba.utils.exceptions import PromptNotPresent, UnknownSiteChosen
from pyba.utils.load_yaml import load_config

config = load_config("general")


class Engine(BaseEngine):
    """
    The main entrypoint for browser automation. This engine exposes the main entry point which is the run() method

    Args:
        `openai_api_key`: API key for OpenAI models should you want to use that
        `vertexai_project_id`: Create a VertexAI project to use that instead of OpenAI
        `vertexai_server_location`: VertexAI server location
        `gemini_api_key`: API key for Gemini-2.5-pro native support without VertexAI
        `headless`: Choose if you want to run in the headless mode or not
        `handle_dependencies`: Choose if you want to automatically install dependencies during runtime
        `use_logger`: Choose if you want to use the logger (that is enable logging of data)
        `enable_tracing`: Choose if you want to enable tracing. This will create a .zip file which you can use in traceviewer
        `trace_save_directory`: The directory where you want the .zip file to be saved
        `max_depth`: The maximum number of actions that you want the model to execute
        `database`: An instance of the Database class which will define all database specific configs
        `model_name`: The model name which you want to run. The default is set to None (because it depends on the provider).

    Find these default values at `pyba/config.yaml`.

    The `Engine` is inherited off from the `BaseEngine`. The BaseEngine handles the common methods for
    all the modes (default, DFS and BFS). The main `Engine` decides if execution needs to be passed to a different
    mode depending on what is set by the user.

    """

    def __init__(
        self,
        openai_api_key: str = None,
        vertexai_project_id: str = None,
        vertexai_server_location: str = None,
        gemini_api_key: str = None,
        headless: bool = config["main_engine_configs"]["headless_mode"],
        handle_dependencies: bool = config["main_engine_configs"]["handle_dependencies"],
        use_random: bool = config["main_engine_configs"]["use_random"],
        use_logger: bool = config["main_engine_configs"]["use_logger"],
        enable_tracing: bool = config["main_engine_configs"]["enable_tracing"],
        trace_save_directory: str = None,
        max_depth: int = config["main_engine_configs"]["max_iteration_steps"],
        database: Database = None,
        model_name: str = None,
        low_memory: bool = False,
    ):
        self.mode = "Normal"
        # Passing the common setup to the BaseEngine
        super().__init__(
            headless=headless,
            enable_tracing=enable_tracing,
            trace_save_directory=trace_save_directory,
            database=database,
            use_random=use_random,
            use_logger=use_logger,
            mode=self.mode,
            handle_dependencies=handle_dependencies,
            openai_api_key=openai_api_key,
            vertexai_project_id=vertexai_project_id,
            vertexai_server_location=vertexai_server_location,
            gemini_api_key=gemini_api_key,
            model_name=model_name,
            low_memory=low_memory,
        )

        self.max_depth = max_depth
        # session_id stays here becasue BaseEngine will be inherited by many
        self.session_id = uuid.uuid4().hex

        selectors = tuple(config["process_config"]["selectors"])
        self.combined_selector = ", ".join(selectors)

    async def run(
        self,
        prompt: str = None,
        automated_login_sites: List[str] = None,
        extraction_format: BaseModel = None,
    ):
        """
        The most basic implementation for the run function

        Args:
            `prompt`: The user's instructions. This is a well defined instruction.
            `automated_login_sites`: A list of sites that you want the model to automatically login to using env credentials
            `extraction_format`: A pydantic BaseModel which defines the extraction format for any data extraction

        Note:

        The `extraction_format` will be decided based on every action. For example:

        ```python3
        from pydantic import BaseModel
        from pyba import Engine

        task = "Go to hackernews. For each post, extract the title, number of upvotes and comments, and the description too"

        class Output(BaseModel):
            # Using optional is a good idea in case the things you're looking for don't exist
            title: Optional[str],
            num_upvotes: Optional[int],
            num_comments: Optional[int],
            desc: Optional[str]

        engine = Engine(**kwargs)

        await engine.run(task, extraction_format=Output)
        ```

        would return data **during** the execution, and now once it finishes. It will dump it in the database as well, and it
        decides if data needs to be extracted on an action basis.

        Using this feature will NOT cost you any more tokens than usual.
        """
        if prompt is None:
            raise PromptNotPresent()

        if automated_login_sites is not None:
            assert isinstance(
                automated_login_sites, list
            ), "Make sure the automated_login_sites is a list!"

            for engine in automated_login_sites:
                # Each engine is going to be a name like "instagram"
                if hasattr(LoginEngine, engine):
                    engine_class = getattr(LoginEngine, engine)
                    self.automated_login_engine_classes.append(engine_class)
                else:
                    raise UnknownSiteChosen(LoginEngine.available_engines())
        try:
            async with Stealth().use_async(async_playwright()) as p:
                self.browser = await p.chromium.launch(**self._launch_kwargs)

                self.context = await self.get_trace_context()
                self.page = await self.context.new_page()
                cleaned_dom = await initial_page_setup(self.page)
                previous_action = None

                for steps in range(0, self.max_depth):
                    login_attempted_successfully = await self.attempt_login()
                    if login_attempted_successfully:
                        cleaned_dom = await self.successful_login_clean_and_get_dom()
                        continue

                    action = self.fetch_action(
                        cleaned_dom=cleaned_dom.to_dict(),
                        user_prompt=prompt,
                        previous_action=previous_action,
                        extraction_format=extraction_format,
                        fail_reason=None,
                        action_status=True,
                    )
                    output = await self.generate_output(
                        action=action, cleaned_dom=cleaned_dom, prompt=prompt
                    )

                    if output:
                        await self.save_trace()
                        await self.shut_down()
                        return output

                    self.log.action(serialize_action(action))

                    value, fail_reason = await perform_action(self.page, action)

                    if value is None:
                        if self.db_funcs:
                            self.db_funcs.push_to_episodic_memory(
                                session_id=self.session_id,
                                action=serialize_action(action),
                                page_url=str(self.page.url),
                                action_status=False,
                                fail_reason=fail_reason,
                            )
                        cleaned_dom = await self.extract_dom()

                        output = await self.retry_perform_action(
                            cleaned_dom=cleaned_dom.to_dict(),
                            prompt=prompt,
                            previous_action=serialize_action(action),
                            action_status=False,
                            fail_reason=fail_reason,
                        )

                        if output:
                            await self.save_trace()
                            await self.shut_down()
                            return output
                    else:
                        if self.db_funcs:
                            self.db_funcs.push_to_episodic_memory(
                                session_id=self.session_id,
                                action=serialize_action(action),
                                page_url=str(self.page.url),
                                action_status=True,
                                fail_reason=None,
                            )

                    previous_action = serialize_action(action)
                    cleaned_dom = await self.extract_dom()
        finally:
            await self.save_trace()
            await self.shut_down()

    def sync_run(
        self,
        prompt: str = None,
        automated_login_sites: List[str] = None,
        extraction_format: BaseModel = None,
    ) -> Union[str, None]:
        """
        Sync endpoint for running the above function
        """
        output = asyncio.run(
            self.run(
                prompt=prompt,
                automated_login_sites=automated_login_sites,
                extraction_format=extraction_format,
            )
        )

        if output:
            return output
