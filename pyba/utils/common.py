import json
import math
from collections import Counter
from typing import List
from urllib.parse import urlparse

from playwright.async_api import Page

from pyba.utils.exceptions import CannotResolveError
from pyba.utils.structure import CleanedDOM, PasswordManager


def url_entropy(url) -> int:
    """
    Computes the Shannon entropy of a URL useful for determining which URLs to
    keep during the general DOM href extraction
    """
    counts = Counter(url)
    total = len(url)
    return -sum((count / total) * math.log2(count / total) for count in counts.values())


def is_absolute_url(url: str) -> bool:
    """
    Determines if a URL is absolute or relative. Used in fixing relative URLs
    in case of goto actions in playwright
    """
    parsed = urlparse(url)
    return bool(parsed.scheme and parsed.netloc)


async def initial_page_setup(page: Page) -> CleanedDOM:
    """
    Helper function for initial page setup and navigation.
    """
    start_page = "https://search.brave.com"

    await page.goto(start_page)

    cleaned_dom = CleanedDOM(
        hyperlinks=[],
        input_fields=["#searchbox"],
        clickable_fields=[],
        actual_text=None,
        current_url=start_page,
    )

    return cleaned_dom


def serialize_action(action) -> str:
    """
    Serializes a PlaywrightAction (SimpleNamespace or Pydantic model) into a
    clean JSON string containing only the non-null fields.
    """
    if hasattr(action, "model_dump"):
        raw = action.model_dump(exclude_none=True)
    else:
        raw = {k: v for k, v in vars(action).items() if v is not None}
    return json.dumps(raw)


def verify_login_page(page_url: str, url_list: List[str]):
    """
    Helper function called inside login engines

    Args:
        page_url: The page URL to be checked against a known list
        url_list: The known URL list for login sites for the specific website

    Returns:
        bool: Whether this page is one of the login pages or not

    Note: This assumes that all the urls in the url_list are ending with a "/".
    """
    parsed = urlparse(page_url)
    normalized_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"

    if not normalized_url.endswith("/"):
        normalized_url += "/"

    return normalized_url in url_list


def extract_secrets(secret_manager: PasswordManager = None) -> dict[str, str]:
    if secret_manager is None:
        return {}

    if not hasattr(secret_manager, "resolve"):
        raise NotImplementedError(
            "Password manager must implement a resolve() -> dict[str, str] method"
        )

    try:
        secrets = secret_manager.resolve()
    except TypeError:
        raise CannotResolveError()

    if not isinstance(secrets, dict):
        raise TypeError("resolve() must return dict[str, str]")

    return secrets
