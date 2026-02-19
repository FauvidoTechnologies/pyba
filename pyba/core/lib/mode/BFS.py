import asyncio
import uuid
from typing import List, Union

from playwright.async_api import async_playwright
from playwright_stealth import Stealth
from pydantic import BaseModel

from pyba.core.agent import PlannerAgent
from pyba.core.helpers.mem_dsl import MemDSL
from pyba.core.lib.action import perform_action
from pyba.core.lib.mode.base import BaseEngine
from pyba.core.scripts import LoginEngine
from pyba.database import Database
from pyba.utils.common import (  # serialize_action kept for db pushes
    initial_page_setup,
    serialize_action,
)
from pyba.utils.exceptions import UnknownSiteChosen
from pyba.utils.load_yaml import load_config

config = load_config("general")


class BFS(BaseEngine):
    """
    Methods for handling BFS exploratory searches. The `BaseEngine` initialises
    the provider and with that the playwright action and output agents.

    This is another entry point engine and can be directly imported by the user.

    The following params are defined:

    Args:
        openai_api_key: API key for OpenAI models should you want to use that
        vertexai_project_id: Create a VertexAI project to use that instead of OpenAI
        vertexai_server_location: VertexAI server location
        gemini_api_key: API key for Gemini-2.5-pro native support without VertexAI
        headless: Choose if you want to run in the headless mode or not
        handle_dependencies: Choose if you want to automatically install dependencies during runtime
        use_logger: Choose if you want to use the logger (that is enable logging of data)
        max_depth: The maximum depth to go into for each plan, where each level of depth corresponds to an action
        max_breadth: The number of plans to execute one by one in depth
        enable_tracing: Choose if you want to enable tracing. This will create a .zip file which you can use in traceviewer
        trace_save_directory: The directory where you want the .zip file to be saved

        database: An instance of the Database class which will define all database specific configs
        model_name: The model name which you want to run. The default is set to None (because it depends on the provider).

    Find these default values at `pyba/config.yaml`.
    """

    def __init__(
        self,
        openai_api_key: str = None,
        vertexai_project_id: str = None,
        vertexai_server_location: str = None,
        gemini_api_key: str = None,
        headless: bool = config["main_engine_configs"]["headless_mode"],
        handle_dependencies: bool = config["main_engine_configs"]["handle_dependencies"],
        use_logger: bool = config["main_engine_configs"]["use_logger"],
        max_depth: int = config["main_engine_configs"]["max_depth"],
        max_breadth: int = config["main_engine_configs"]["max_breadth"],
        enable_tracing: bool = config["main_engine_configs"]["enable_tracing"],
        trace_save_directory: str = None,
        database: Database = None,
        model_name: str = None,
        low_memory: bool = config["main_engine_configs"]["minimize_memory"],
    ):
        self.mode = "BFS"
        # Passing the common setup to the BaseEngine
        super().__init__(
            headless=headless,
            enable_tracing=enable_tracing,
            trace_save_directory=trace_save_directory,
            database=database,
            use_logger=use_logger,
            mode=self.mode,
            openai_api_key=openai_api_key,
            vertexai_project_id=vertexai_project_id,
            vertexai_server_location=vertexai_server_location,
            gemini_api_key=gemini_api_key,
            model_name=model_name,
            low_memory=low_memory,
        )

        # session_id is per-engine, not in BaseEngine, because BaseEngine is shared across modes
        self.session_id = uuid.uuid4().hex

        self.planner_agent = PlannerAgent(engine=self)

        self.max_depth = max_depth
        self.max_breadth = max_breadth

    async def _run(
        self, task: str, extraction_format: BaseModel = None, context_id: str = None
    ) -> Union[str, None]:
        """
        helper run function for BFS

        Args:
            task: A singular task which needs to be performed
            extraction_format: The extraction format for the required goal
            context_id: A dynamically generated context-id for each browser window

        Since BFS generates multiple browser windows at runtime, each gets its own context ID
        to manage individual exponential retries and logging.
        """
        try:
            async with Stealth().use_async(async_playwright()) as p:
                browser = await p.chromium.launch(**self._launch_kwargs)

                context = await self.get_trace_context(browser_instance=browser)
                page = await context.new_page()
                cleaned_dom = await initial_page_setup(page)
                mem = MemDSL()

                for _ in range(0, self.max_depth):
                    login_attempted_successfully = await self.attempt_login(page)
                    if login_attempted_successfully:
                        cleaned_dom = await self.successful_login_clean_and_get_dom()
                        continue

                    action = self.fetch_action(
                        cleaned_dom=cleaned_dom.to_dict(),
                        user_prompt=task,
                        action_history=mem.history,
                        extraction_format=extraction_format,
                        context_id=context_id,
                        action_status=True,
                        fail_reason=None,
                    )
                    output = await self.generate_output(
                        action=action, cleaned_dom=cleaned_dom, prompt=task
                    )
                    if output:
                        await self.save_trace()
                        await self.shut_down()
                        return output

                    value, fail_reason = await perform_action(page, action)
                    line = mem.record(action, success=value is not None, fail_reason=fail_reason)
                    self.log.action(line)

                    if value is None:
                        if self.db_funcs:
                            self.db_funcs.push_to_bfs_episodic_memory(
                                session_id=self.session_id,
                                context_id=context_id,
                                action=serialize_action(action),
                                page_url=str(page.url),
                            )
                        cleaned_dom = await self.extract_dom(page)
                        output = await self.retry_perform_action(
                            cleaned_dom=cleaned_dom.to_dict(),
                            prompt=task,
                            action_history=mem.history,
                            action_status=False,
                            fail_reason=fail_reason,
                            page=page,
                            mem=mem,
                        )
                        if output:
                            await self.save_trace(context)
                            await self.shut_down(context, browser)
                            return output
                    else:
                        if self.db_funcs:
                            self.db_funcs.push_to_bfs_episodic_memory(
                                session_id=self.session_id,
                                context_id=context_id,
                                action=serialize_action(action),
                                page_url=str(page.url),
                            )

                    cleaned_dom = await self.extract_dom(page)

                self.log.warning(
                    "The maximum depth for the current task has been reached, generating a new plan to achieve this task"
                )
        finally:
            await self.save_trace(context)
            await self.shut_down(context, browser)

    async def run(
        self,
        prompt: str,
        automated_login_sites: List[str] = None,
        extraction_format: BaseModel = None,
    ) -> List:
        """
        The async run function

        Args:
            prompt: The prompt which needs to be converted to plans
            automated_login_sites: List of names for which sites to login automatically
            extraction_format: The extraction format for any extraction that needs to be done

        Returns:
            List
        """

        if automated_login_sites is not None:
            assert isinstance(automated_login_sites, list), (
                "Make sure the automated_login_sites is a list!"
            )

            for engine in automated_login_sites:
                # Each engine is going to be a name like "instagram"
                if hasattr(LoginEngine, engine):
                    engine_class = getattr(LoginEngine, engine)
                    self.automated_login_engine_classes.append(engine_class)
                else:
                    raise UnknownSiteChosen(LoginEngine.available_engines())

        plan_list = self.planner_agent.generate(task=prompt)

        assert isinstance(plan_list, list), (
            f"Expected the plan to be a list, got {type(plan_list)} instead."
        )

        self.log.info(f"This is the plan for a BFS: {plan_list}")

        # Keeping this purely async is better for playwright
        tasks = []
        for task in plan_list:
            context_id = uuid.uuid4().hex  # This should do it.
            tasks.append(asyncio.create_task(self._run(task, extraction_format, context_id)))
        results = await asyncio.gather(*tasks, return_exceptions=False)

        return results

    def sync_run(
        self,
        prompt: str,
        automated_login_sites: List[str] = None,
        extraction_format: BaseModel = None,
    ):
        """
        Synchronous endpoint for running BFS mode.

        Args:
            prompt: The prompt which needs to be converted to plans
            automated_login_sites: List of names for which sites to login automatically
            extraction_format: The extraction format for any extraction that needs to be done
        """
        try:
            output = asyncio.run(
                self.run(
                    prompt=prompt,
                    automated_login_sites=automated_login_sites,
                    extraction_format=extraction_format,
                )
            )

            if output:
                return output
        except KeyboardInterrupt:
            # This is a forced shutdown, silently let it slip
            pass
