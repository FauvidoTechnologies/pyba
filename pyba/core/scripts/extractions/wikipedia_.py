from pathlib import Path
from typing import List, Dict
from urllib.parse import urlparse, unquote

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
        self.main_config = load_config("general")["main_engine_configs"]

        # The javascript to be executed for links
        js_file_path = Path(__file__).parent.parent / "js/extractions.js"
        self.js_function_string = js_file_path.read_text()

    def _add_indices(self, articles: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        The returned articles from the JS execution are already ordered. This method
        is to bring that point home by adding an index param to the Dictionaries
        """
        return [{"index": i + 1, **article} for i, article in enumerate(articles)]

    def _minimize_token_effort(self, articles: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        All the links in wikipedia can be categorized into two types:

        1. English article links: `https://en.wikipedia.org/wiki/{article_name}`)
        2. Other languages: `https://{language_code}.wikipedia.org/wiki/{article_name}`

        This method assumes only the english language (case 1), and hence the model
        only needs to see the title and the article_name. The construction of the URL
        can be done through the code itself once it outputs its selection.
        """
        for _ in articles:
            href = _.get("href")
            parsed = urlparse(href)
            article = parsed.path.removeprefix("/wiki/")
            _["href"] = unquote(article)

        return articles

    async def extract_links_and_titles(self) -> List[Dict[str, str]]:
        """
        This method extracts all the titles and their links from any wikipedia page using
        the same javascript described above.

        Return object: [
            {"title": "Some title", "href": "link"},
            {"title": "Some other title", "href": "some other link"},
            ...
        ]

        In case of wikipedia, we implement a token minimization technique. See,
        `_minimize_token_effort`.
        """
        articles = await self.page.evaluate(self.js_function_string, self.config)

        # This is a potentailly breaking change because the model MIGHT not format
        # The article correctly.
        # TODO: FIX THIS ASAP
        if self.main_config["minimize_tokens"]:
            return self._minimize_token_effort(articles)

        articles = self._add_indices(articles)
        return articles

    async def extract(self) -> List[Dict[str, str]]:
        articles = await self.extract_links_and_titles()
        return articles
