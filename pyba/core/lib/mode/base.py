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

    async def extract_dom(self):
        """
        Extracts the relevant fields from the DOM of the current page and returns
        the DOM dataclass.
        """
        self.mouse = MouseMovements(page=self.page)
        self.scroll_manager = ScrollMovements(page=self.page)

        try:
            await self.wait_till_loaded()
            page_html = await self.page.content()
        except Exception:
            # We might get a "Unable to retrieve content because the page is navigating and changing the content" exception
            # This might happen because page.content() will start and issue an evaluate, while the page is reloading and making network calls
            # So, once it gets a response, it commits it and clears the execution contents so page.content() fails.
            # See https://github.com/microsoft/playwright/issues/16108

            # We might choose to wait for networkidle -> https://github.com/microsoft/playwright/issues/22897
            try:
                await self.wait_till_loaded()
            except Exception:
                # If networkidle never happens, then we'll try a direct wait
                await asyncio.sleep(3)

            page_html = await self.page.content()

        try:
            body_text = await self.page.inner_text("body")
            elements = await self.page.query_selector_all(self.combined_selector)
            base_url = self.page.url
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
            page=self.page,
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

    async def save_trace(self):
        """
        Endpoint to save the trace if required
        """
        if self.tracing:
            trace_path = self.trace_dir / f"{self.session_id}_trace.zip"
            try:
                await self.context.tracing.stop(path=str(trace_path))
                self.log.info(f"This is the tracepath: {trace_path}")
            except Exception:
                # Abrupt browser closure
                pass

    async def shut_down(self):
        """
        Function to cleanly close the existing browsers and contexts. This also saves
        the traces in the provided trace_dir by the user or the default.
        """
        try:
            await self.context.close()
            await self.browser.close()
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

    async def get_trace_context(self):
        """
        Helper function to intialise the context using the Tracing class

        Return:
            `context`: The playwright to be used for automation
        """

        tracing = Tracing(
            browser_instance=self.browser,
            session_id=self.session_id,
            enable_tracing=self.tracing,
            trace_save_directory=self.trace_save_directory,
        )

        self.trace_dir = tracing.trace_dir
        context = await tracing.initialize_context()

        return context

    async def attempt_login(self) -> bool:
        """
        Helper function to attempt and perform a login to chosen sites

        Returns:
            `flag`: A boolean to indicate the success or failure for the attempt

        The login attempt may fail due to two reasons:

            - The current page is not a login page
            - Some selectors changed due to which the login engine returned None

        Note that the LoginEngines are hardcoded engines for speed.
        """

        flag = False

        if self.automated_login_engine_classes:
            for engine in self.automated_login_engine_classes:
                engine_instance = engine(self.page)
                self.log.info(f"Testing for {engine_instance.engine_name} login engine")
                # Instead of just running it and checking inside, we can have a simple lookup list
                out_flag = await engine_instance.run()
                if out_flag:
                    # This means it was True and we successfully logged in
                    self.log.success(f"Logged in successfully through the {self.page.url} link")
                    flag = True
                    break
                elif out_flag is None:
                    # This means it wasn't for a login page for this engine
                    pass
                else:
                    # This means it failed
                    self.log.warning(f"Login attempted at {self.page.url} but failed!")

        return flag

    async def successful_login_clean_and_get_dom(self):
        """
        Helper function to obtain the cleaned_dom after a successful login

        Functionality:

        - Cleans the automated_login_engine_classes list (that is, we're assuming only 1 login session
        for each run)
        - Gets the latest page contents and parses the DOM using the extraction engine
        """

        self.automated_login_engine_classes = None
        self.mouse = MouseMovements(page=self.page)
        self.scroll_manager = ScrollMovements(page=self.page)
        # Update the DOM after a login
        try:
            await self.wait_till_loaded()
        except Exception:
            await asyncio.sleep(2)

        page_html = await self.page.content()
        body_text = await self.page.inner_text("body")
        elements = await self.page.query_selector_all(self.combined_selector)
        base_url = self.page.url

        extraction_engine = ExtractionEngines(
            html=page_html,
            body_text=body_text,
            elements=elements,
            base_url=base_url,
            page=self.page,
        )
        cleaned_dom = await extraction_engine.extract_all()
        cleaned_dom.current_url = base_url

        return cleaned_dom

    def fetch_history(self) -> str:
        """
        Helper function to obtain the history of actions

        Returns:
            `history`: The last successful action element or ""
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
        history: str,
        extraction_format: BaseModel = None,
        context_id: str = None,
    ):
        """
        Helper function to fetch an actionable PlaywrightResponse element

        Args:
            `cleaned_dom`: The DOM for the current page
            `user_prompt`: The actual task given by the user
            `history`: The last action performed by the model
            `extraction_format`: The extraction format requested by the user.
            `context_id`: A unique identifier for this browser window (useful when multiple windows)

        For an explanation of the `extraction_format` read the main file documentation.

        Returns:
            `action`: An actionable playwrightresponse element
        """

        try:
            action = self.playwright_agent.process_action(
                cleaned_dom=cleaned_dom,
                user_prompt=user_prompt,
                history=history,
                extraction_format=extraction_format,
                context_id=context_id,
            )
        except Exception as e:
            self.log.error(f"something went wrong in obtaining the response: {e}")
            action = None

        return action

    async def retry_perform_action(
        self,
        cleaned_dom: Dict,
        prompt: str,
        history: str,
        fail_reason: str,
        extraction_format: BaseModel = None,
    ) -> Optional[str]:
        """
        helper function to retry the action after a failure

        Args:
            `cleaned_dom`: The new cleaned DOM for the current page
            `prompt`: The original prompt given by the user
            `history`: The past action that failed
            `fail_reason`: Reason for the failure for the action
            `extraction_format`: In case the current page needs extraction as well

        This function will retry the action based on the current DOM and the past action. This should
        most likely fix the issue of a stale element or a hallucinated component or something.

        Return:
            `output`: If the action was successful and automation is completed
            `None`: The usual case where an action is performed
        """

        self.log.warning("The previous action failed, checking the latest page")
        action = self.playwright_agent.process_action(
            cleaned_dom=cleaned_dom,
            user_prompt=prompt,
            history=history,
            fail_reason=fail_reason,
            extraction_format=extraction_format,
        )

        output = await self.generate_output(action=action, cleaned_dom=cleaned_dom, prompt=prompt)

        if output:
            return output

        self.log.action(action)

        if self.db_funcs:
            self.db_funcs.push_to_episodic_memory(
                session_id=self.session_id,
                action=str(action),
                page_url=str(self.page.url),
            )

        await perform_action(self.page, action)

    async def wait_till_loaded(self):
        """
        Helper function to wait till load state while applying
        random jitters (if specified by the user)
        """
        if self.use_random_flag:
            await asyncio.gather(
                self.page.wait_for_load_state("networkidle", timeout=1000),
                self.mouse.random_movement(),
                self.scroll_manager.apply_scroll_jitters(),
            )  # Wait for a second for network calls to stablize
        else:
            (await self.page.wait_for_load_state("networkidle", timeout=1000),)
