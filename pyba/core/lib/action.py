import asyncio
import re
from urllib.parse import urljoin

from playwright._impl._errors import Error
from playwright.async_api import Page

import pyba.core.helpers as global_vars
from pyba.core.helpers.jitters import MouseMovements, ScrollMovements
from pyba.logger import get_logger
from pyba.utils.common import is_absolute_url
from pyba.utils.structure import PlaywrightAction


class PlaywrightActionPerformer:
    """
    The playwright automation class. To add new handles, make a function here
    and define that under perform()

    Below is an exhaustive set of playwright actions that the handler will manage and the dispatcher will execute

    1. Navigation functions
        - handle_navigation
        - handle_back
        - handle_forward
        - handle_reload

    2. Interaction functions
        - handle_input
        - handle_typing
        - handle_click
        - handle_double_click
        - handle_hover
        - handle_checkboxes
        - handle_select
        - handle_file_upload

    3. Keyboard/mouse functions
        - handle_press
        - handle_keyboard_press
        - handle_keyboard_type
        - handle_mouse_move
        - handle_mouse_click

    4. Scrolling
        - handle_scrolling

    5. Waits
        - handle_wait

    6. Javascript functions
        - handle_evaluate_js
        - handle_screenshot
        - handle_download

    7. New pages
        - handle_switch_page
        - handle_new_page
        - handle_close_page

    """

    def __init__(self, page: Page, action: PlaywrightAction):
        self.page = page
        self.action = action

        self.log = get_logger()
        self.mouse = MouseMovements(page=self.page)
        self.scroll_manager = ScrollMovements(page=self.page)

        self.use_random_flag = global_vars._use_random

    async def wait_till_loaded(self):
        if self.use_random_flag:
            await asyncio.gather(
                self.page.wait_for_load_state("domcontentloaded"),
                self.mouse.random_movement(),
                self.scroll_manager.apply_scroll_jitters(),
            )
        else:
            (await self.page.wait_for_load_state("domcontentloaded"),)

    # -----------------
    # Handle navigation
    # -----------------
    async def handle_navigation(self):
        """
        Handles browser navigation by opening new websites.
        Waits until the page is loaded.
        """
        await self.page.goto(self.action.goto)
        await self.wait_till_loaded()

    async def handle_back(self):
        if self.use_random_flag:
            await asyncio.gather(
                self.page.go_back(wait_until="domcontentloaded"),
                self.mouse.random_movement(),
                self.scroll_manager.apply_scroll_jitters(),
            )
        else:
            await self.page.go_back(wait_until="domcontentloaded")

    async def handle_forward(self):
        if self.use_random_flag:
            await asyncio.gather(
                self.page.go_forward(wait_until="domcontentloaded"),
                self.mouse.random_movement(),
                self.scroll_manager.apply_scroll_jitters(),
            )
        else:
            await self.page.go_forward(wait_until="domcontentloaded")

    async def handle_reload(self):
        if self.use_random_flag:
            await asyncio.gather(
                self.page.reload(wait_until="domcontentloaded"),
                self.mouse.random_movement(),
                self.scroll_manager.apply_scroll_jitters(),
            )
        else:
            await self.page.reload(wait_until="domcontentloaded")

    # -------------------
    # Handle interactions
    # -------------------
    async def handle_input(self):
        """
        Inputs a value to a selector field
        """
        await self.page.fill(self.action.fill_selector, self.action.fill_value)

    async def handle_typing(self):
        await self.page.type(self.action.type_selector, self.action.type_text)

    async def handle_click(self):
        """
        Handles clicking elements. Has additional checks to ensure that
        the element is not actually a relational hyperlink.

        This is done in the following ways:

        - We first check if the click element is actually an <a> tag
        - Or if it has a closest ancestor <a> tag

        In either case we extract the href from that <a> tag and directly goto that
        """
        click_target = self.action.click
        if click_target is None:
            return

        # Handle absolute URLs: if the click string contains a full URL, extract and navigate to it.
        url_match = re.search(r"https?://[^\s'\"]+", click_target)
        if url_match:
            href = url_match.group(0)
            await self.page.goto(href)
            await self.wait_till_loaded()
            return

        locator = self.page.locator(click_target)

        try:
            await locator.scroll_into_view_if_needed()
        except Exception:
            pass

        # Trying to find a hyperlink element (the target or its ancestor)
        # https://playwright.dev/python/docs/api/class-locator#locator-evaluate -> Tests a javascript expression
        try:
            href = await locator.evaluate(
                """
                el => {
                    let link = el.tagName.toLowerCase() === 'a' ? el : el.closest('a');
                    return link ? link.getAttribute('href') : null;
                }
            """
            )
        except Error:
            # Catching a strict mode violation and defaulting to the first click
            # Unfortunately playwright errors aren't fully specific
            try:
                first_locator = locator.first
                href = await first_locator.evaluate(
                    """
                    el => {
                        let link = el.tagName.toLowerCase() === 'a' ? el : el.closest('a');
                        return link ? link.getAttribute('href') : null;
                    }
                    """,
                    timeout=5000,
                )
            except Exception as e:
                raise e
        if href:
            # Handling relative links by checking for a schema and a netloc (host + optional port)
            if not is_absolute_url(href):
                base_url = "/".join(self.page.url.split("/")[0:3])
                href = urljoin(base_url, href)
            await self.page.goto(href)
            await self.wait_till_loaded()
            return
        else:
            try:
                await locator.click(timeout=1000)
            except Error as e:  # Another strict mode violation
                if "strict mode violation" in str(e):
                    try:
                        first_locator = locator.first
                        await first_locator.click(force=True, timeout=1000)
                    except Exception as e:
                        raise e
                elif "Timeout 1000ms exceeded" in str(e):
                    raise e  # For it to be caught later
            except Exception as e:
                raise e

    async def handle_dropdown_click(self):
        """
        Dispatch function to handle dropdown menus. This function requires both
        the field_id and the field_value to be specified in the single action.
        """
        field_id = self.action.dropdown_field_id
        field_value = self.action.dropdown_field_value

        await self.page.locator(field_id).select_option(label=f"{field_value}")

    async def handle_right_click(self):
        """
        Dispatch function to handle a right click
        """
        await self.page.click(self.action.right_click, button="right")

    async def handle_double_click(self):
        """
        Handles double clicking an element.
        """
        await self.page.dblclick(self.action.dblclick)

    async def handle_hover(self):
        """
        Handles hovering over an element to make new actions visible.
        """
        await self.page.hover(self.action.hover)

    async def handle_checkboxes(self):
        if self.action.check:
            await self.page.check(self.action.check)
        if self.action.uncheck:
            await self.page.uncheck(self.action.uncheck)

    async def handle_select(self):
        await self.page.select_option(
            self.action.select_selector,
            value=self.action.select_value,
        )

    async def handle_file_upload(self):
        await self.page.set_input_files(
            self.action.upload_selector,
            self.action.upload_path,
        )

    # ----------------------------------
    # Handle mouse/keyboard interactions
    # ----------------------------------
    async def handle_press(self):
        """
        Handles a key press.
        """
        # If a specific selector is provided, press the key on that element.
        if self.action.press_selector and self.action.press_key:
            await self.page.press(self.action.press_selector, self.action.press_key)
        # If no selector is provided, press the key on the entire page.
        elif self.action.press_key:
            await self.page.keyboard.press(self.action.press_key)

    async def handle_keyboard_press(self):
        """
        Handles a keyboard press action on the entire page.
        """
        await self.page.keyboard.press(self.action.keyboard_press)

    async def handle_keyboard_type(self):
        await self.page.keyboard.type(self.action.keyboard_type)

    async def handle_mouse_move(self):
        await self.page.mouse.move(self.action.mouse_move_x or 0, self.action.mouse_move_y or 0)

    async def handle_mouse_click(self):
        await self.page.mouse.click(self.action.mouse_click_x or 0, self.action.mouse_click_y or 0)

    # ----------------
    # Handle scrolling
    # ----------------
    async def handle_scrolling(self):
        """
        Automates manual scrolling (or scrolls to center)
        """
        x = self.action.scroll_x or 0
        y = self.action.scroll_y or 0
        await self.page.mouse.wheel(x, y)

    # ------------
    # Handle waits
    # ------------
    async def handle_wait(self):
        if self.action.wait_selector:
            if self.use_random_flag:
                await asyncio.gather(
                    self.page.wait_for_selector(
                        self.action.wait_selector,
                        timeout=self.action.wait_timeout or 1000,
                    ),
                    self.mouse.random_movement(),
                    self.scroll_manager.apply_scroll_jitters(),
                )
            else:
                await self.page.wait_for_selector(
                    self.action.wait_selector, timeout=self.action.wait_timeout or 1000
                )
        elif self.action.wait_ms:
            if self.use_random_flag:
                await asyncio.gather(
                    asyncio.sleep(self.action.wait_ms / 1000),
                    self.mouse.random_movement(),
                    self.scroll_manager.apply_scroll_jitters(),
                )
            else:
                (await asyncio.sleep(self.action.wait_ms / 1000),)

    # ---------------------------
    # Handle Javascript functions
    # ---------------------------
    async def handle_evaluate_js(self):
        """
        Handles the evaluation of Javascript in the browser environment
        and brings the result back to the code.

        This is the recommended way to using it.
        ```js
        const href = await page.evaluate(() => document.location.href);
        ```

        We strip the js snippet here for any return statements because those
        aren't required for inline functions.
        """

        if self.action.evaluate_js.startswith("return"):
            self.action.evaluate_js = " ".join(self.action.evaluate_js.split(" ")[1:])
        result = await self.page.evaluate(self.action.evaluate_js)

        self.log.info(f"[JS Evaluation Result]: {result}")
        return result

    async def handle_screenshot(self):
        await self.page.screenshot(path=self.action.screenshot_path, full_page=True)

    async def handle_download(self):
        async with self.page.expect_download() as download_info:
            await self.page.click(self.action.download_selector)
        download = await download_info.value
        path = await download.path()
        self.log.info(f"Downloaded to: {path}")

    # -------------------
    # Handling new pages
    # -------------------
    async def handle_switch_page(self):
        context = self.page.context
        pages = context.pages
        if self.action.switch_page_index is not None and self.action.switch_page_index < len(
            pages
        ):
            self.page = pages[self.action.switch_page_index]
            await self.page.bring_to_front()

    async def handle_new_page(self):
        context = self.page.context
        new_page = await context.new_page()
        mouse = MouseMovements(page=new_page)
        await new_page.goto(self.action.new_page)
        await asyncio.gather(
            new_page.wait_for_load_state("domcontentloaded"), mouse.random_movement()
        )
        self.page = new_page

    async def handle_close_page(self):
        await self.page.close()

    # ----------
    # Dispatcher
    # ----------
    async def perform(self) -> None:
        """
        The main dispatch function.

        All handlers are called here as and when required by the AI models.
        Contains an exhaustive list of all the functions that can be chosen
        during the automation process
        """
        a = self.action

        if a.goto:
            return await self.handle_navigation()
        if a.go_back:
            return await self.handle_back()
        if a.go_forward:
            return await self.handle_forward()
        if a.reload:
            return await self.handle_reload()
        if a.fill_selector and a.fill_value is not None:
            return await self.handle_input()
        if a.type_selector and a.type_text:
            return await self.handle_typing()
        if a.click:
            return await self.handle_click()
        if a.dblclick:
            return await self.handle_double_click()
        if a.dropdown_field_id:
            return await self.handle_dropdown_click()
        if a.right_click:
            return await self.handle_right_click()
        if a.hover:
            return await self.handle_hover()
        if a.press_selector or a.press_key:
            return await self.handle_press()
        if a.keyboard_press:
            return await self.handle_keyboard_press()
        if a.keyboard_type:
            return await self.handle_keyboard_type()
        if a.check or a.uncheck:
            return await self.handle_checkboxes()
        if a.select_selector and a.select_value:
            return await self.handle_select()
        if a.upload_selector and a.upload_path:
            return await self.handle_file_upload()
        if a.scroll_x or a.scroll_y:
            return await self.handle_scrolling()
        if a.wait_selector or a.wait_ms:
            return await self.handle_wait()
        if a.evaluate_js:
            return await self.handle_evaluate_js()
        if a.screenshot_path:
            return await self.handle_screenshot()
        if a.download_selector:
            return await self.handle_download()
        if a.new_page:
            return await self.handle_new_page()
        if a.close_page:
            return await self.handle_close_page()
        if a.switch_page_index is not None:
            return await self.handle_switch_page()


async def perform_action(page: Page, action: PlaywrightAction):
    """
    The entry point function
    """
    performer = PlaywrightActionPerformer(page, action)

    try:
        await performer.perform()
        return True, None  # The fail_reason is None
    except Exception as e:
        return None, e
