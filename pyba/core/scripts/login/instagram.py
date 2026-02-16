import asyncio

from dotenv import load_dotenv
from playwright.async_api import Page

from pyba.utils.load_yaml import load_config

from .base import BaseLogin

load_dotenv()  # Loading the username and passwords
config = load_config("general")["automated_login_configs"]["instagram"]

screen_height = config["click_location"]["default_screen_height"]
x_from_left = config["click_location"]["x_from_left"]
y_from_bottom = config["click_location"]["y_from_bottom"]
y_top_left = screen_height - y_from_bottom


class InstagramLogin(BaseLogin):
    """
    The instagram login engine, inherits from the BaseLogin class.
    """

    def __init__(self, page: Page) -> None:
        super().__init__(page, engine_name="instagram")

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
            try:
                # Alternate fields that instagram uses
                await asyncio.gather(
                    self.page.wait_for_selector(self.config["fallback"]["username_selector"]),
                    self.mouse.random_movement(),
                    self.scroll_manager.apply_scroll_jitters(),
                )
                await self.page.fill(self.config["fallback"]["username_selector"], self.username)
                await self.page.fill(self.config["fallback"]["password_selector"], self.password)
                await self.page.click(self.config["submit_selector"])
            except Exception:
                return False

        try:
            await asyncio.gather(
                self.page.wait_for_selector(
                    self.config["additional_args"]["additional_selector_1"], timeout=30000
                ),
                self.mouse.random_movement(),
                self.scroll_manager.apply_scroll_jitters(),
            )
            await self.page.click(self.config["additional_args"]["additional_selector_1"])
        except Exception:
            pass

        try:
            await asyncio.gather(
                self.page.wait_for_selector(
                    self.config["additional_args"]["additional_selector_2"], timeout=10000
                ),
                self.mouse.random_movement(),
                self.scroll_manager.apply_scroll_jitters(),
            )
            await self.page.mouse.click(x_from_left, y_top_left)
        except Exception:
            pass

        return True
