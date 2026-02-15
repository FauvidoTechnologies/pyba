from pathlib import Path

from playwright.async_api import Page

from pyba.utils.load_yaml import load_config


class WikipediaDOMExtraction:
    """
    Specialized class for handling extractions in wikipedia which is
    bundled with links	and text and whatnot.

    The goal of the class is to correctly and informatively display
    the relevant results to the main model.
    """

    def __init__(self, page: Page):
        """
        Executes the link extraction javascript in the browser page

        We need the following things from any wikipedia site:

        1. All the links
        2. All the text (with no placeholders for images or such cause we don't
                care about that right now)
        3. Search result (for when searches are performed) links
        """
        self.page = page

        self.config = load_config("extraction")["wikipedia"]

        # The javascript to be executed for links
        js_file_path = Path(__file__).parent.parent / "js/extractions.js"
        self.js_function_string = js_file_path.read_text()

    async def extract_links_and_titles(self):
        """
        This method extracts all the titles and their links from any wikipedia page using
        the same javascript described above.

        Note: We're stripping away certain URLs which are pretty useless
        """
        pass
