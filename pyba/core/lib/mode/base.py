import asyncio
import json
from typing import Dict, Optional, Literal

from playwright.async_api import TimeoutError
from pydantic import BaseModel

import pyba.core.helpers as global_vars
from pyba.core.agent import PlaywrightAgent
from pyba.core.helpers.jitters import MouseMovements, ScrollMovements
from pyba.core.lib import HandleDependencies
from pyba.core.lib.action import perform_action
from pyba.core.lib.code_generation import CodeGeneration
from pyba.core.provider import Provider
from pyba.core.scripts import ExtractionEngines
from pyba.core.tracing import Tracing
from pyba.database import DatabaseFunctions
from pyba.logger import setup_logger, get_logger
from pyba.utils.exceptions import DatabaseNotInitialised


class BaseEngine:
    """
    A reusable base class that encapsulates the shared browser lifecycle,
    tracing, DOM extraction, and utility helpers.

        The following will be initialised by the BaseEngine:

        - `db_funcs`: The database functions to be used for inserting and querying logs
        - `mode`: The mode of operation (DFS, BFS or Normal)
        - `provider_instance`: This will detect the provider you're using
        - `playwright_agent`: The actual playwright brains of the operation
    """

    def __init__(
        self,
        headless: bool = True,
        enable_tracing: bool = True,
        trace_save_directory: str = None,
        database=None,
        use_random=None,
        use_logger: bool = None,
        mode: Literal["DFS", "BFS", "Normal"] = None,
        handle_dependencies: bool = False,
        openai_api_key: str = None,
        vertexai_project_id: str = None,
        vertexai_server_location: str = None,
        gemini_api_key: str = None,
    ):
        self.headless_mode = headless
        self.tracing = enable_tracing
        self.trace_save_directory = trace_save_directory

        self.mode = mode
        self.database = database
        self.db_funcs = DatabaseFunctions(self.database) if database else None

        self.automated_login_engine_classes = []

        self.use_random_flag = (
            use_random if use_random else False
        )  # I like to set defaults as None...
        global_vars._use_random = (
            self.use_random_flag
        )  # Update the global use random for other modules

        setup_logger(use_logger=use_logger)
        self.log = get_logger()

        provider_instance = Provider(
            openai_api_key=openai_api_key,
            gemini_api_key=gemini_api_key,
            vertexai_project_id=vertexai_project_id,
            vertexai_server_location=vertexai_server_location,
        )

        self.provider = provider_instance.provider
        self.model = provider_instance.model
        self.openai_api_key = provider_instance.openai_api_key
        self.gemini_api_key = provider_instance.gemini_api_key
        self.vertexai_project_id = provider_instance.vertexai_project_id
        self.location = provider_instance.location

        # Defining the playwright agent with the defined configs
        self.playwright_agent = PlaywrightAgent(engine=self)

        if handle_dependencies:
            HandleDependencies.playwright.handle_dependencies()

    async def run(self):
        """
        Run function which will be defined inside all child classes
        """
        pass

    async def extract_dom(self, page=None):
        """
        Extracts the relevant fields from the DOM of the current page and returns
        the DOM dataclass. This is backwards compatible with Engine and DFS while
        it supports BFS by pinning the page down.

        Args:
            `page`: Optional argument to pin the page for removing self dependency
        """
        page_obj = page if page is not None else self.page
        self.mouse = MouseMovements(page=page_obj)
        self.scroll_manager = ScrollMovements(page=page_obj)

        try:
            await self.wait_till_loaded(page_obj)
            page_html = await page_obj.content()
        except Exception:
            # We might get a "Unable to retrieve content because the page is navigating and changing the content" exception
            # This might happen because page.content() will start and issue an evaluate, while the page is reloading and making network calls
            # So, once it gets a response, it commits it and clears the execution contents so page.content() fails.
            # See https://github.com/microsoft/playwright/issues/16108

            # We might choose to wait for networkidle -> https://github.com/microsoft/playwright/issues/22897
            try:
                await self.wait_till_loaded(page_obj)
            except Exception:
                # If networkidle never happens, then we'll try a direct wait
                await asyncio.sleep(3)

            page_html = await page_obj.content()

        try:
            body_text = await page_obj.inner_text("body")
            elements = await page_obj.query_selector_all(self.combined_selector)
            base_url = page_obj.url
        except TimeoutError:
            self.log.error("The page has not loaded within the defined timeout, going back")
            return None

        # Then we need to extract the new cleaned_dom from the page
        # Passing in known_fields for the input fields that we already know off so that
        # its easier for the extraction engine to work
        extraction_engine = ExtractionEngines(
            html=page_html,
            body_text=body_text,
            elements=elements,
            base_url=base_url,
            page=page_obj,
        )

        # Perform an all out extraction
        cleaned_dom = await extraction_engine.extract_all()
        cleaned_dom.current_url = base_url
        return cleaned_dom

    async def generate_output(self, action, cleaned_dom, prompt):
        """
        Helper function to generate the output if the action
        has been completed.

        Args:
            `action`: The action as given out by the model
            `cleaned_dom`: The latest cleaned_dom for the model to read
            `prompt`: The prompt which was given to the model
        """
        if action is None or all(value is None for value in vars(action).values()):
            self.log.success("Automation completed, agent has returned None")
            try:
                output = self.playwright_agent.get_output(
                    cleaned_dom=cleaned_dom.to_dict(), user_prompt=prompt
                )
                self.log.info(f"This is the output given by the model: {output}")
                return output
            except Exception:
                # This should rarely happen
                await asyncio.sleep(10)
                output = self.playwright_agent.get_output(
                    cleaned_dom=cleaned_dom.to_dict(), user_prompt=prompt
                )
                self.log.info(f"This is the output given by the model: {output}")
                return output
        else:
            return None

    async def save_trace(self, context=None):
        """
        Endpoint to save the trace if required. This is backwards compatible for Engine
        and DFS while is supports BFS by removing the self dependency

        Args:
            `context`: Optional argument to pin the browser context down
        """
        context_obj = context if context is not None else self.context
        if self.tracing:
            trace_path = self.trace_dir / f"{self.session_id}_trace.zip"
            try:
                await context_obj.tracing.stop(path=str(trace_path))
                self.log.info(f"This is the tracepath: {trace_path}")
            except Exception:
                # Abrupt browser closure
                pass

    async def shut_down(self, context=None, browser=None):
        """
        Function to cleanly close the existing browsers and contexts. This also saves
        the traces in the provided trace_dir by the user or the default.

        This is backwards compatible for Engine and DFS while is supports BFS by
        removing the self dependency

        Args:
            `context`: Optional argument to pin the specific brower context down
            `browser`: Optional argument to pin the browser instance down
        """
        context_obj = context if context is not None else self.context
        browser_obj = browser if browser is not None else self.browser
        try:
            await context_obj.close()
            await browser_obj.close()
        except Exception:
            # Context/browser have already been closed
            pass

    def generate_code(self, output_path: str) -> bool:
        """
        Function end-point for code generation

        Args:
            `output_path`: output file path to save the generated code to
        """
        if not self.db_funcs:
            raise DatabaseNotInitialised()

        codegen = CodeGeneration(
            session_id=self.session_id, output_path=output_path, database_funcs=self.db_funcs
        )
        codegen.generate_script()
        self.log.info(f"Created the script at: {output_path}")
        return True

    async def get_trace_context(self, browser_instance=None):
        """
        Helper function to intialise the context using the Tracing class. This is backwards compatible
        for Engine and DFS while is supports BFS by removing the self dependency

        Args:
            `browser_instance`: Optional argument to pin the browser session down

        Return:
            `context`: The playwright to be used for automation
        """

        tracing = Tracing(
            browser_instance=browser_instance if browser_instance is not None else self.browser,
            session_id=self.session_id,
            enable_tracing=self.tracing,
            trace_save_directory=self.trace_save_directory,
        )

        self.trace_dir = tracing.trace_dir
        context = await tracing.initialize_context()

        return context

    async def attempt_login(self, page=None) -> bool:
        """
        Helper function to attempt and perform a login to chosen sites. This is backwards compatible
        with Engine and DFS while it supports BFS by pinning the page down.

        Args:
            `page`: Optional argument to pin the page for removing self dependency

        Returns:
            `flag`: A boolean to indicate the success or failure for the attempt

        The login attempt may fail due to two reasons:

            - The current page is not a login page
            - Some selectors changed due to which the login engine returned None

        Note that the LoginEngines are hardcoded engines for speed.
        """

        flag = False
        page_obj = page if page is not None else self.page
        if self.automated_login_engine_classes:
            for engine in self.automated_login_engine_classes:
                engine_instance = engine(page_obj)
                self.log.info(f"Testing for {engine_instance.engine_name} login engine")
                # Instead of just running it and checking inside, we can have a simple lookup list
                out_flag = await engine_instance.run()
                if out_flag:
                    # This means it was True and we successfully logged in
                    self.log.success(f"Logged in successfully through the {page_obj.url} link")
                    flag = True
                    break
                elif out_flag is None:
                    # This means it wasn't for a login page for this engine
                    pass
                else:
                    # This means it failed
                    self.log.warning(f"Login attempted at {page_obj.url} but failed!")

        return flag

    async def successful_login_clean_and_get_dom(self, page=None):
        """
        Helper function to obtain the cleaned_dom after a successful login. This is backwards compatible
        with Engine and DFS while it supports BFS by pinning the page down.

        Args:
            `page`: Optional argument to pin the page for removing self dependency

        Functionality:

        - Cleans the automated_login_engine_classes list (that is, we're assuming only 1 login session
        for each run)
        - Gets the latest page contents and parses the DOM using the extraction engine
        """
        page_obj = page if page is not None else self.page

        self.automated_login_engine_classes = None
        self.mouse = MouseMovements(page=page_obj)
        self.scroll_manager = ScrollMovements(page=page_obj)
        # Update the DOM after a login
        try:
            await self.wait_till_loaded()
        except Exception:
            await asyncio.sleep(2)

        page_html = await page_obj.content()
        body_text = await page_obj.inner_text("body")
        elements = await page_obj.query_selector_all(self.combined_selector)
        base_url = page_obj.url

        extraction_engine = ExtractionEngines(
            html=page_html,
            body_text=body_text,
            elements=elements,
            base_url=base_url,
            page=page_obj,
        )
        cleaned_dom = await extraction_engine.extract_all()
        cleaned_dom.current_url = base_url

        return cleaned_dom

    def fetch_history(self) -> str:
        """
        Helper function to obtain the history of actions.

        TODO: This functions should fetch the last k history elements and use them as `history` and
        NOT previous_action. The previous_action and its status must be stored regardless.

        Returns:
            `history`: The last logged action
        """

        try:
            # Get history if db_funs is defined, that is, Databases are being used
            history = None
            if self.db_funcs:
                history = self.db_funcs.get_episodic_memory_by_session_id(
                    session_id=self.session_id
                )

            history = json.loads(history.actions)[-1] if history else ""
        except Exception as e:
            self.log.warning(f"Couldn't query the database for history: {e}")
            history = ""

        return history

    def fetch_action(
        self,
        cleaned_dom: Dict,
        user_prompt: str,
        previous_action: str,
        extraction_format: BaseModel = None,
        context_id: str = None,
        fail_reason: str = None,
        action_status: bool = None,
    ):
        """
        Helper function to fetch an actionable PlaywrightResponse element

        Args:
            `cleaned_dom`: The DOM for the current page
            `user_prompt`: The actual task given by the user
            `previous_action`: The last action performed by the model
            `extraction_format`: The extraction format requested by the user.
            `context_id`: A unique identifier for this browser window (useful when multiple windows)
            `fail_reason`: The reason for the failure of the previous action
            `action_status`: A boolean to indicate if the previous action was successful or not

        For an explanation of the `extraction_format` read the main file documentation.

        Returns:
            `action`: An actionable playwrightresponse element
        """

        try:
            # Each process-action call is to be passed the status of the previous call
            action = self.playwright_agent.process_action(
                cleaned_dom=cleaned_dom,
                user_prompt=user_prompt,
                previous_action=previous_action,
                extraction_format=extraction_format,
                context_id=context_id,
                fail_reason=fail_reason,
                action_status=action_status,
            )
        except Exception as e:
            self.log.error(f"something went wrong in obtaining the response: {e}")
            action = None

        return action

    async def retry_perform_action(
        self,
        cleaned_dom: Dict,
        prompt: str,
        previous_action: str,
        action_status: bool,
        fail_reason: str,
        extraction_format: BaseModel = None,
        page=None,
    ) -> Optional[str]:
        """
        helper function to retry the action after a failure. This is backwards compatible with Engine
        and DFS while it supports BFS by pinning the page down.


        Args:
            `cleaned_dom`: The new cleaned DOM for the current page
            `prompt`: The original prompt given by the user
            `previous_action`: The past action that failed
            `action_status`: A boolean to indicate the failure of the action (I know, not needed but let's keep it for now!)
            `fail_reason`: Reason for the failure for the action
            `extraction_format`: In case the current page needs extraction as well
            `page`: Optional argument to pin the page down to remove self dependency

        This function will retry the action based on the current DOM and the past action. This should
        most likely fix the issue of a stale element or a hallucinated component or something.

        Return:
            `output`: If the action was successful and automation is completed
            `None`: The usual case where an action is performed
        """
        page_obj = page if page is not None else self.page

        self.log.warning("The previous action failed, checking the latest page")
        action = self.playwright_agent.process_action(
            cleaned_dom=cleaned_dom,
            user_prompt=prompt,
            previous_action=previous_action,
            fail_reason=fail_reason,
            extraction_format=extraction_format,
            action_status=action_status,
        )

        output = await self.generate_output(action=action, cleaned_dom=cleaned_dom, prompt=prompt)

        if output:
            return output

        self.log.action(action)

        # Deprecated. We now log data before calling retry action
        # if self.db_funcs:
        #     self.db_funcs.push_to_episodic_memory(
        #         session_id=self.session_id,
        #         action=str(action),
        #         page_url=str(page_obj.url),
        #     )

        await perform_action(page_obj, action)

    async def wait_till_loaded(self, page=None):
        """
        Helper function to wait till load state while applying random jitters
        (if specified by the user). This is backwards compatible with Engine
        and DFS while it supports BFS by pinning the page down.

        Args:
            `page`: Optional argument to pin the page for removing self dependency
        """
        page_obj = page if page is not None else self.page
        if self.use_random_flag:
            await asyncio.gather(
                page_obj.wait_for_load_state("networkidle", timeout=1000),
                self.mouse.random_movement(),
                self.scroll_manager.apply_scroll_jitters(),
            )  # Wait for a second for network calls to stablize
        else:
            (await page_obj.wait_for_load_state("networkidle", timeout=1000),)
