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
from pyba.utils.common import (  # serialize_action kept for db pushes
    initial_page_setup,
    serialize_action,
)
from pyba.utils.exceptions import PromptNotPresent, UnknownSiteChosen
from pyba.utils.load_yaml import load_config

config = load_config("general")


class Step(BaseEngine):
    """
    Step-by-step browser automation. The user controls the loop externally
    by calling start(), step(), and stop().

    Args:
        openai_api_key: API key for OpenAI models should you want to use that
        vertexai_project_id: Create a VertexAI project to use that instead of OpenAI
        vertexai_server_location: VertexAI server location
        gemini_api_key: API key for Gemini-2.5-pro native support without VertexAI
        use_random: Enables mouse and scroll randomisations to evade bot detection
        headless: Choose if you want to run in the headless mode or not
        handle_dependencies: Choose if you want to automatically install dependencies during runtime
        use_logger: Choose if you want to use the logger (that is enable logging of data)
        enable_tracing: Choose if you want to enable tracing. This will create a .zip file which you can use in traceviewer
        trace_save_directory: The directory where you want the .zip file to be saved
        database: An instance of the Database class which will define all database specific configs
        get_output: When True, asks the model for a summarised output when a step completes. When False (default), step() silently returns None on completion
        model_name: The model name which you want to run. The default is set to None (because it depends on the provider).
    """

    def __init__(
        self,
        openai_api_key: str = None,
        vertexai_project_id: str = None,
        vertexai_server_location: str = None,
        gemini_api_key: str = None,
        headless: bool = False,
        handle_dependencies: bool = config["main_engine_configs"]["handle_dependencies"],
        use_random: bool = config["main_engine_configs"]["use_random"],
        use_logger: bool = config["main_engine_configs"]["use_logger"],
        enable_tracing: bool = config["main_engine_configs"]["enable_tracing"],
        trace_save_directory: str = None,
        max_actions_per_step: int = 5,
        database: Database = None,
        get_output: bool = False,
        model_name: str = None,
        low_memory: bool = config["main_engine_configs"]["minimize_memory"],
    ):
        self.mode = "STEP"
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

        self.session_id = uuid.uuid4().hex
        selectors = tuple(config["process_config"]["selectors"])
        self.combined_selector = ", ".join(selectors)
        self.max_actions_per_step = max_actions_per_step

        self._cleaned_dom = None
        self._playwright_context_manager = None
        self._pw = None
        self.get_output = get_output

    async def start(self, automated_login_sites: List[str] = None):
        """
        Creates a persistent browser instance. This needs to be explicitly called
        by the user when using the Step mode. This handles the automated login
        for us as well.
        """
        if automated_login_sites is not None:
            assert isinstance(automated_login_sites, list), (
                "Make sure the automated_login_sites is a list!"
            )
            for engine in automated_login_sites:
                if hasattr(LoginEngine, engine):
                    self.automated_login_engine_classes.append(getattr(LoginEngine, engine))
                else:
                    raise UnknownSiteChosen(LoginEngine.available_engines())

        self._playwright_context_manager = Stealth().use_async(async_playwright())
        self._pw = await self._playwright_context_manager.__aenter__()
        self.browser = await self._pw.chromium.launch(**self._launch_kwargs)
        self.context = await self.get_trace_context()
        self.page = await self.context.new_page()
        self._cleaned_dom = await initial_page_setup(self.page)

    async def step(
        self, prompt_step: str, extraction_format: BaseModel = None
    ) -> Union[str, None]:
        """
        The step function is a replica of the `Engine.run()`. It passes the full action history
        into context and tries to figure out the best way to achieve the short term prompt given by the user.

        Args:
            prompt_step: A single stepwise prompt given by the user (This might require more than one steps)
            extraction_format: The final extraction format IF NEEDED
        """
        if prompt_step is None:
            raise PromptNotPresent()

        for _ in range(self.max_actions_per_step):
            login_attempted_successfully = await self.attempt_login()
            if login_attempted_successfully:
                self._cleaned_dom = await self.successful_login_clean_and_get_dom()
                continue

            action = self.fetch_action(
                cleaned_dom=self._cleaned_dom.to_dict(),
                user_prompt=prompt_step,
                action_history=self.mem.history,
                extraction_format=extraction_format,
                fail_reason=None,
                action_status=True,
            )

            if self.get_output:
                output = await self.generate_output(
                    action=action, cleaned_dom=self._cleaned_dom, prompt=prompt_step
                )
                if output:
                    return output

            if not action:
                return None

            value, fail_reason = await perform_action(self.page, action)
            line = self.mem.record(action, success=value is not None, fail_reason=fail_reason)
            self.log.action(line)

            if value is None:
                if self.db_funcs:
                    self.db_funcs.push_to_episodic_memory(
                        session_id=self.session_id,
                        action=serialize_action(action),
                        page_url=str(self.page.url),
                        action_status=False,
                        fail_reason=fail_reason,
                    )
                self._cleaned_dom = await self.extract_dom()

                output = await self.retry_perform_action(
                    cleaned_dom=self._cleaned_dom.to_dict(),
                    prompt=prompt_step,
                    action_history=self.mem.history,
                    action_status=False,
                    fail_reason=fail_reason,
                )
                if output:
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

            self._cleaned_dom = await self.extract_dom()

        return None

    async def stop(self):
        """
        Kills the persistent browser instance once called. For using the Step engine, this NEEDS
        to be called explicitly by the user in order to close the instance.
        """
        try:
            await self.save_trace()
            await self.shut_down()
        finally:
            if self._playwright_context_manager:
                await self._playwright_context_manager.__aexit__(None, None, None)

    # Some helper functions for sync endpoints
    # Note that using these will be a little weirder in the main pipeline.
    def sync_start(self, automated_login_sites: List[str] = None):
        asyncio.run(self.start(automated_login_sites=automated_login_sites))

    def sync_step(self, prompt_step: str, extraction_format: BaseModel = None) -> Union[str, None]:
        return asyncio.run(self.step(prompt_step=prompt_step, extraction_format=extraction_format))

    def sync_stop(self):
        asyncio.run(self.stop())
