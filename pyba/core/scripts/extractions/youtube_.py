from pathlib import Path
from typing import List, Dict

from playwright.async_api import Page

from pyba.utils.load_yaml import load_config


class YouTubeDOMExtraction:
    """
    Extracts links along with their texts from a youtube page. This is specifically designed for youtube pages, and can be used
    either when a search result is queried and videos are being browsed or when a video is playing and something else needs to
    be clicked.

    This provides an exhaustive list of the valid selectors and buttons which are needed for interacting on YouTube.
    """

    def __init__(self, page: Page):
        """
        Evaluates javascript inside the browser page

        1. links on the page along with their titles (for all visible videos)
        2. input fields for searches and comments
        3. Buttons for like and dislike etc.
        """
        self.page = page
        self.config = load_config("extraction")["youtube"]

        js_file_path = Path(__file__).parent.parent / "js/extractions.js"
        self.js_function_string = js_file_path.read_text()

    async def extract_links_and_titles(self) -> List[Dict[str, str]]:
        """
        Extracts all the video links and their title names from a YouTube page. It checks for
        all possible `/watch?v=` type selectors and queries their names. Uses vanilla
        Javascript executed in the browser session to get all the results.

        Returns:
            List[Dict[str, str]]: List of dictionaries with "title" and "href" keys
        """

        videos = await self.page.evaluate(self.js_function_string, self.config)
        return videos

    async def extract(self):
        videos = await self.extract_links_and_titles()
        return videos
