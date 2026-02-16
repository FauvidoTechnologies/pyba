import asyncio

from playwright.async_api import Page

from pyba.core.scripts.login.base import BaseLogin


class GmailLogin(BaseLogin):
    """
    The gmail login engine, inherits from the BaseLogin engine
    """

    def __init__(self, page: Page) -> None:
        super().__init__(page, engine_name="gmail")

    async def _perform_login(self) -> bool:
        try:
            await asyncio.gather(
                self.page.wait_for_selector(self.config["username_selector"]),
                self.mouse.random_movement(),
                self.scroll_manager.apply_scroll_jitters(),
            )
            await self.page.fill(self.config["username_selector"], self.username)
            await self.page.click(self.config["submit_selector"])
        except Exception:
            return False

        try:
            await asyncio.gather(
                self.page.wait_for_selector(self.config["password_selector"]),
                self.mouse.random_movement(),
                self.scroll_manager.apply_scroll_jitters(),
            )
            await self.page.fill(self.config["password_selector"], self.password)
            await self.page.click(self.config["submit_selector"])
        except Exception:
            try:
                # Alternate fields that gmail might use
                await asyncio.gather(
                    self.page.wait_for_selector(self.config["fall_back"]["password_selector"]),
                    self.mouse.random_movement(),
                    self.scroll_manager.apply_scroll_jitters(),
                )
                await self.page.fill(self.config["fall_back"]["password_selector"], self.password)
                await self.page.click(self.config["submit_selector"])
            except Exception:
                return False

        return True
