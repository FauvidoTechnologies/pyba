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
from pyba.utils.common import initial_page_setup
from pyba.utils.exceptions import PromptNotPresent, UnknownSiteChosen
from pyba.utils.load_yaml import load_config

config = load_config("general")


class Step(BaseEngine):
    """
    Step-by-step browser automation. The user controls the loop externally
    by calling start(), step(), and stop().
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
        )

        self.session_id = uuid.uuid4().hex
        selectors = tuple(config["process_config"]["selectors"])
        self.combined_selector = ", ".join(selectors)
        self.max_actions_per_step = max_actions_per_step

        self._cleaned_dom = None
        self._playwright_context_manager = None
        self._pw = None

    async def start(self, automated_login_sites: List[str] = None):
        """
        Creates a persistent browser instance. This needs to be explicitly called
        by the user when using the Step mode. This handles the automated login
        for us as well.
        """
        if automated_login_sites is not None:
            assert isinstance(
                automated_login_sites, list
            ), "Make sure the automated_login_sites is a list!"
            for engine in automated_login_sites:
                if hasattr(LoginEngine, engine):
                    self.automated_login_engine_classes.append(getattr(LoginEngine, engine))
                else:
                    raise UnknownSiteChosen(LoginEngine.available_engines())

        self._playwright_context_manager = Stealth().use_async(async_playwright())
        self._pw = await self._playwright_context_manager.__aenter__()
        self.browser = await self._pw.chromium.launch(headless=self.headless_mode)
        self.context = await self.get_trace_context()
        self.page = await self.context.new_page()
        self._cleaned_dom = await initial_page_setup(self.page)

    async def step(
        self, prompt_step: str, extraction_format: BaseModel = None
    ) -> Union[str, None]:
        """
        The step function is a replica of the `Engine.run()`. It takes in the previous action as well
        into context and tries to figure out the best way to achieve the short term prompt given by the user.

        Args:
            `prompt_step`: A single step wise prompt given by the user (This might require more than one steps)
            `extraction_format`: The final extraction format IF NEEDED
        """
        if prompt_step is None:
            raise PromptNotPresent()

        previous_action = None

        for _ in range(self.max_actions_per_step):
            login_attempted_successfully = await self.attempt_login()
            if login_attempted_successfully:
                self._cleaned_dom = await self.successful_login_clean_and_get_dom()
                continue

            action = self.fetch_action(
                cleaned_dom=self._cleaned_dom.to_dict(),
                user_prompt=prompt_step,
                previous_action=previous_action,
                extraction_format=extraction_format,
                fail_reason=None,
                action_status=True,
            )

            output = await self.generate_output(
                action=action, cleaned_dom=self._cleaned_dom, prompt=prompt_step
            )
            if output:
                return output

            self.log.action(action)
            value, fail_reason = await perform_action(self.page, action)

            if value is None:
                if self.db_funcs:
                    self.db_funcs.push_to_episodic_memory(
                        session_id=self.session_id,
                        action=str(action),
                        page_url=str(self.page.url),
                        action_status=False,
                        fail_reason=fail_reason,
                    )
                self._cleaned_dom = await self.extract_dom()

                output = await self.retry_perform_action(
                    cleaned_dom=self._cleaned_dom.to_dict(),
                    prompt=prompt_step,
                    previous_action=str(action),
                    action_status=False,
                    fail_reason=fail_reason,
                )
                if output:
                    return output
            else:
                if self.db_funcs:
                    self.db_funcs.push_to_episodic_memory(
                        session_id=self.session_id,
                        action=str(action),
                        page_url=str(self.page.url),
                        action_status=True,
                        fail_reason=None,
                    )

            previous_action = str(action)
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
    # Note that using these will be a little weireder in the main pipeline.
    def sync_start(self, automated_login_sites: List[str] = None):
        asyncio.run(self.start(automated_login_sites=automated_login_sites))

    def sync_step(self, prompt_step: str, extraction_format: BaseModel = None) -> Union[str, None]:
        return asyncio.run(self.step(prompt_step=prompt_step, extraction_format=extraction_format))

    def sync_stop(self):
        asyncio.run(self.stop())
