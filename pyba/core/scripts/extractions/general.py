from pathlib import Path
from typing import List
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.async_api import Page

from pyba.logger import get_logger
from pyba.utils.common import url_entropy
from pyba.utils.load_yaml import load_config
from pyba.utils.structure import CleanedDOM

general_config = load_config("general")
config = load_config("extraction")[
    "general"
]  # This means we're referring to the general extraction class


class GeneralDOMExtraction:
    """
    Given the DOM from the URL, this class provides functions to extract it properly

    1. Extract all the hyperlinks from it
    2. Extract all input_fields from it (basically all fillable boxes)
    3. Extract all the clickables from it
    4. Extract all the actual text from it (we don't have to do any OCR for this!)

    Note that extracting all clickable elements might get messy so we'll use that only when
    the total length is lower than a certain threshold.

    This is the general extraction. Some specific websites require a different way to do this.
    """

    def __init__(
        self,
        html: str,
        body_text: str,
        page: Page,
        base_url: str = None,
        clickable_fields_flag: bool = False,
    ) -> None:
        self.html = html
        self.body_text = body_text
        self.page = page
        self.base_url = base_url

        self.log = get_logger()
        self.clickable_fields_flag = clickable_fields_flag

        js_path = Path(__file__).parent.parent / "js/input_fields.js"
        self._input_fields_js = js_path.read_text()

    def _extract_clickables(self) -> List[dict]:
        soup = BeautifulSoup(self.html, "html.parser")
        candidates = []

        for tag in soup.find_all(
            list(config["extraction_configs"]["clickables"]["clickable_field_selectors"])
        ):
            if tag.name == "a":
                href = tag.get("href", "").strip().lower()
                if (
                    not href
                    or href
                    in set(
                        config["extraction_configs"]["clickables"][
                            "invalid_selector_field_hyperlinks"
                        ]
                    )
                    or href.startswith("javascript:")
                    or href.startswith("#")
                ):
                    continue
            candidates.append(tag)

        for tag in soup.find_all("input"):
            t = tag.get("type", "").lower()
            if t in tuple(
                config["extraction_configs"]["clickables"]["valid_button_types_for_clickables"]
            ):
                candidates.append(tag)

        candidates += soup.find_all(attrs={"onclick": True})
        candidates += soup.find_all(
            attrs={"role": lambda v: v and v.lower() in ("button", "link")}
        )
        candidates += soup.find_all(attrs={"tabindex": True})

        seen = set()
        results = []
        for el in candidates:
            key = (el.name, str(el))
            if key in seen:
                continue
            seen.add(key)

            href = el.get("href")
            onclick = el.get("onclick")
            role = el.get("role")
            tabindex = el.get("tabindex")
            text = el.get_text(strip=True)

            if not (text or href or onclick):
                continue

            if href and self.base_url:
                href = urljoin(self.base_url, href)

            junk_keywords = config["extraction_configs"]["clickables"]["junk_keywords"]
            if any(k in text.lower() for k in junk_keywords):
                continue

            results.append(
                {
                    "tag": el.name,
                    "text": text,
                    "href": href,
                    "onclick": onclick,
                    "role": role,
                    "tabindex": tabindex,
                    "outer_html": str(el)[:1000],
                }
            )

        # Cleaning this up based on outer_html

        cleaned = []
        for el in results:
            data = {k: v for k, v in el.items() if v and k != "outer_html"}
            cleaned.append(data)

        return cleaned

    def _extract_href(self) -> List[str]:
        soup = BeautifulSoup(str(self.html), "html.parser")
        hrefs = [a["href"].strip() for a in soup.find_all("a", href=True)]

        clean_hrefs = []
        for href in hrefs:
            href_lower = href.lower()

            # If we do a raw extraction, all this junk will make it through
            if (
                not href_lower
                or href_lower
                in set(
                    config["extraction_configs"]["clickables"]["invalid_selector_field_hyperlinks"]
                )
                or href_lower.startswith("javascript:")
                or href_lower.startswith("#")
            ):
                continue

            # Convert relative URLs to absolute URLs
            full_url = urljoin(self.base_url, href)

            if any(
                x in href_lower
                for x in list(config["extraction_configs"]["hyperlinks"]["links_to_avoid"])
            ):
                continue

            parsed = urlparse(full_url)
            if parsed.scheme not in set(
                config["extraction_configs"]["hyperlinks"]["valid_schemas"]
            ):
                continue

            clean_hrefs.append(full_url)

        # Filter URLs based on entropy to remove URLs with random IDs
        # URLs with high entropy (typically > 5) contain random strings that provide
        # no additional context to the model

        output = [href for href in clean_hrefs if url_entropy(href) < 5.0]
        return output

    async def _extract_all_text(self) -> List:
        lines = self.body_text.split("\n")
        non_empty_lines = [line.strip() for line in lines if line.strip()]
        return non_empty_lines

    async def _extract_input_fields(self) -> List[dict]:
        """
        Extracts fillable input fields using a single browser-side JS evaluation.
        Checks readOnly, disabled, visibility, tag type, and input type entirely
        in the browser — no round-trips per element, no fill-test-clear.

        Returns:
            List[Dict]: List of valid fillable fields with tag/type/id/name/selector info.
        """
        js_config = {
            "valid_tags": list(config["extraction_configs"]["input_fields"]["valid_tags"]),
            "invalid_input_types": list(
                config["extraction_configs"]["input_fields"]["invalid_input_types"]
            ),
        }

        return await self.page.evaluate(self._input_fields_js, js_config)

    async def extract(self) -> CleanedDOM:
        """
        Runs all extraction functions and returns a unified cleaned_dom dictionary.

        Returns:
            CleanedDOM: A dataclass containing hyperlinks, input fields, clickable fields, and text content.
        """
        cleaned_dom = CleanedDOM()

        try:
            cleaned_dom.hyperlinks = self._extract_href()
        except Exception as e:
            cleaned_dom.hyperlinks = []
            self.log.error(f"Failed to extract hyperlinks: {e}")

        try:
            if self.clickable_fields_flag:
                cleaned_dom.clickable_fields = self._extract_clickables()
            else:
                cleaned_dom.clickable_fields = self._extract_clickables()[:10]
        except Exception as e:
            cleaned_dom.clickable_fields = []
            self.log.error(f"Failed to extract clickables: {e}")

        try:
            cleaned_dom.actual_text = await self._extract_all_text()
        except Exception as e:
            cleaned_dom.actual_text = []
            self.log.error(f"Failed to extract text: {e}")

        try:
            cleaned_dom.input_fields = await self._extract_input_fields()
        except Exception as e:
            cleaned_dom.input_fields = []
            self.log.error(f"Failed to extract input fields: {e}")

        return cleaned_dom
