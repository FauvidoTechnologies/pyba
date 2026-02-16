import asyncio
import os
import urllib.parse
from abc import ABC, abstractmethod
from typing import Optional

from dotenv import load_dotenv
from playwright.async_api import Page

import pyba.core.helpers as global_vars
from pyba.core.helpers.jitters import MouseMovements, ScrollMovements
from pyba.utils.common import verify_login_page
from pyba.utils.exceptions import CredentialsNotSpecified
from pyba.utils.load_yaml import load_config

load_dotenv()  # Loading the username and passwords


class BaseLogin(ABC):
    """
    The base class for all login engines.
    This handles common logic like credential loading, page verification,
    and 2FA waiting.
    """

    def __init__(self, page: Page, engine_name: str) -> None:
        self.page = page
        self.engine_name = engine_name

        self.config = load_config("general")["automated_login_configs"][self.engine_name]
        self.username = os.getenv(f"{self.engine_name}_username")
        self.password = os.getenv(f"{self.engine_name}_password")

        if self.username is None or self.password is None:
            raise CredentialsNotSpecified(self.engine_name)

        self.uses_2FA = self.config["uses_2FA"]
        self.final_2FA_url = self.config["2FA_wait_value"]

        self.mouse = MouseMovements(page=self.page)
        self.scroll_manager = ScrollMovements(page=self.page)
        self.use_random_flag = global_vars._use_random

    @abstractmethod
    async def _perform_login(self) -> bool:
        """
        This will be implemented in the main LoginEngines
        It should return True on success and False on failure.
        """
        raise NotImplementedError

    async def _handle_2fa(self) -> None:
        """
        Blocking wait until the user completes the 2FA step
        by polling the current URL.
        """
        while True:
            current_url = self.page.url
            hostname = urllib.parse.urlparse(current_url).hostname or ""

            if hostname.endswith(
                self.final_2FA_url
            ):  # Only when we reach the required domain name, we'll break
                break

            # Continuous polling
            if self.use_random_flag:
                await asyncio.gather(
                    asyncio.sleep(1),
                    self.mouse.random_movement(),
                    self.scroll_manager.apply_scroll_jitters(),
                )
            else:
                await asyncio.sleep(1)

    async def run(self) -> Optional[bool]:
        """
        The main login execution flow.

        Returns:
            `None` if we're not supposed to launch the automated login script here
            `True/False` if the login was successful or a failure
        """
        val = verify_login_page(page_url=self.page.url, url_list=list(self.config["urls"]))
        if not val:
            return None

        # Run the site-specific login script
        login_successful = await self._perform_login()
        if not login_successful:
            return False

        try:
            if self.use_random_flag:
                await asyncio.gather(
                    self.page.wait_for_load_state("networkidle", timeout=10000),
                    self.mouse.random_movement(),
                    self.scroll_manager.apply_scroll_jitters(),
                )
            else:
                (await self.page.wait_for_load_state("networkidle", timeout=10000),)
        except Exception:
            pass

        if self.uses_2FA:
            await self._handle_2fa()

        return True
