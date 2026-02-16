import asyncio

from playwright.async_api import Page

from pyba.core.scripts.login.base import BaseLogin


class FacebookLogin(BaseLogin):
    """
    The facebook login engine, inherited from the BaseLogin class.
    """

    def __init__(self, page: Page) -> None:
        super().__init__(page, engine_name="facebook")

    async def _perform_login(self) -> bool:
        try:
            await asyncio.gather(
                self.page.wait_for_selector(self.config["username_selector"]),
                self.mouse.random_movement(),
                self.scroll_manager.apply_scroll_jitters(),
            )
            await self.page.fill(self.config["username_selector"], self.username)
            await self.page.fill(self.config["password_selector"], self.password)
            await self.page.click(self.config["submit_selector"])
        except Exception:
            return False

        return True
