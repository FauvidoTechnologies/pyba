import importlib
import json
import sys
from types import SimpleNamespace

import pytest


def _import_common():
    spec = importlib.util.spec_from_file_location(
        "pyba.utils.common",
        "pyba/utils/common.py",
        submodule_search_locations=[],
    )
    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("pyba", type(sys)("pyba"))
    sys.modules.setdefault("pyba.utils", type(sys)("pyba.utils"))
    sys.modules.setdefault("pyba.utils.structure", type(sys)("pyba.utils.structure"))
    setattr(sys.modules["pyba.utils.structure"], "CleanedDOM", None)
    spec.loader.exec_module(mod)
    return mod


common = _import_common()
url_entropy = common.url_entropy
is_absolute_url = common.is_absolute_url
serialize_action = common.serialize_action
verify_login_page = common.verify_login_page


class TestUrlEntropy:
    def test_single_char_is_zero(self):
        assert url_entropy("aaaa") == 0.0

    def test_diverse_url_higher_than_repetitive(self):
        assert url_entropy("https://example.com/path?q=1") > url_entropy("aaaaaaaaaa")

    def test_returns_float(self):
        assert isinstance(url_entropy("https://test.com"), float)

    def test_two_chars_equal_split(self):
        assert url_entropy("ab") == pytest.approx(1.0)


class TestIsAbsoluteUrl:
    def test_https(self):
        assert is_absolute_url("https://example.com") is True

    def test_http(self):
        assert is_absolute_url("http://example.com") is True

    def test_relative_path(self):
        assert is_absolute_url("/about") is False

    def test_bare_path(self):
        assert is_absolute_url("about/page") is False

    def test_empty_string(self):
        assert is_absolute_url("") is False

    def test_scheme_only(self):
        assert is_absolute_url("https://") is False

    def test_with_port(self):
        assert is_absolute_url("http://localhost:8080/path") is True


class TestSerializeAction:
    def test_pydantic_model(self):
        class FakeModel:
            def model_dump(self, exclude_none=False):
                return {"action": "click", "selector": "#btn"}

        result = json.loads(serialize_action(FakeModel()))
        assert result == {"action": "click", "selector": "#btn"}

    def test_simple_namespace(self):
        action = SimpleNamespace(action="goto", url="https://test.com", input_text=None)
        result = json.loads(serialize_action(action))
        assert result == {"action": "goto", "url": "https://test.com"}
        assert "input_text" not in result

    def test_all_none_fields_excluded(self):
        action = SimpleNamespace(a=None, b=None)
        assert json.loads(serialize_action(action)) == {}

    def test_returns_valid_json(self):
        action = SimpleNamespace(x=1)
        json.loads(serialize_action(action))


class TestVerifyLoginPage:
    def test_matching_url(self):
        assert (
            verify_login_page(
                "https://accounts.google.com/login", ["https://accounts.google.com/login/"]
            )
            is True
        )

    def test_trailing_slash_normalized(self):
        assert (
            verify_login_page("https://example.com/login/", ["https://example.com/login/"]) is True
        )

    def test_no_match(self):
        assert (
            verify_login_page("https://example.com/dashboard", ["https://example.com/login/"])
            is False
        )

    def test_query_params_stripped(self):
        assert (
            verify_login_page(
                "https://example.com/login?next=home", ["https://example.com/login/"]
            )
            is True
        )

    def test_empty_url_list(self):
        assert verify_login_page("https://example.com/login", []) is False

    def test_fragment_stripped(self):
        assert (
            verify_login_page("https://example.com/login#section", ["https://example.com/login/"])
            is True
        )
