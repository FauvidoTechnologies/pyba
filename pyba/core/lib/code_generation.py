import json
from typing import Dict, List

from pyba.database import DatabaseFunctions
from pyba.logger import get_logger


class CodeGeneration:
    """
    Create the full automation code used by the model

    - Requires the database to be populated with all the actions
    - Pulls action from the database and writes the script at a user location

    Args:
        session_id: The unique identifier for this session
        output_path: Path to save the code to
        database_funcs: The Database instantiated by the user
    """

    # Selector-value pairs: maps the selector field to its corresponding value field
    SELECTOR_VALUE_PAIRS = {
        "fill_selector": "fill_value",
        "type_selector": "type_text",
        "press_selector": "press_key",
        "select_selector": "select_value",
        "upload_selector": "upload_path",
    }

    # X/Y coordinate pairs: maps the x field to its corresponding y field
    XY_PAIRS = {
        "scroll_x": "scroll_y",
        "mouse_move_x": "mouse_move_y",
        "mouse_click_x": "mouse_click_y",
    }

    # Code templates for each action type
    TEMPLATES = {
        # Navigation
        "goto": 'page.goto("{value}")',
        "go_back": "page.go_back()",
        "go_forward": "page.go_forward()",
        "reload": "page.reload()",
        # Interactions
        "click": 'page.click("{value}")',
        "dblclick": 'page.dblclick("{value}")',
        "hover": 'page.hover("{value}")',
        "right_click": 'page.click("{value}", button="right")',
        "check": 'page.check("{value}")',
        "uncheck": 'page.uncheck("{value}")',
        # Selector + value pairs
        "fill_selector": 'page.fill("{selector}", "{value}")',
        "type_selector": 'page.type("{selector}", "{value}")',
        "press_selector": 'page.press("{selector}", "{value}")',
        "select_selector": 'page.select_option("{selector}", "{value}")',
        "upload_selector": 'page.set_input_files("{selector}", "{value}")',
        # Dropdowns
        "dropdown_field_id": 'page.locator("{selector}").select_option(label="{value}")',
        # Waits
        "wait_selector": 'page.wait_for_selector("{value}", timeout={timeout})',
        "wait_ms": "page.wait_for_timeout({value})",
        # Keyboard and mouse
        "keyboard_press": 'page.keyboard.press("{value}")',
        "keyboard_type": 'page.keyboard.type("{value}")',
        # X/Y pairs
        "scroll_x": "page.mouse.wheel({x}, {y})",
        "mouse_move_x": "page.mouse.move({x}, {y})",
        "mouse_click_x": "page.mouse.click({x}, {y})",
        # Evaluation and utilities
        "evaluate_js": "page.evaluate({value})",
        "screenshot_path": 'page.screenshot(path="{value}")',
        "download_selector": 'with page.expect_download() as download_info:\n    page.click("{value}")\ndownload = download_info.value\ndownload.save_as(download.suggested_filename)',
        # Page management
        "new_page": 'page.context.new_page().goto("{value}")',
        "close_page": "page.close()",
        "switch_page_index": "page = page.context.pages[{value}]",
    }

    def __init__(self, session_id: str, output_path: str, database_funcs: DatabaseFunctions):
        self.session_id = session_id
        self.output_path = output_path
        self.db_funcs = database_funcs
        self.log = get_logger()

    def _get_run_actions(self) -> List[Dict]:
        """
        Queries the database and returns the list of actions as parsed dicts.
        Each action is a dict with only the non-null fields.
        """
        logs = self.db_funcs.get_episodic_memory_by_session_id(session_id=self.session_id)

        if not logs or not logs.actions:
            return []

        raw_actions = json.loads(logs.actions)
        parsed = []
        for entry in raw_actions:
            if isinstance(entry, dict):
                parsed.append(entry)
            elif isinstance(entry, str):
                try:
                    parsed.append(json.loads(entry))
                except json.JSONDecodeError:
                    pass
        return parsed

    def _parse_action_to_code(self, action: Dict) -> str:
        """
        Converts a single action dict into a Playwright code string.
        """
        # Selector + value pairs (fill_selector/fill_value, etc.)
        for selector_field, value_field in self.SELECTOR_VALUE_PAIRS.items():
            if selector_field in action:
                template = self.TEMPLATES[selector_field]
                selector = action[selector_field]
                value = action.get(value_field, "")
                return template.format(selector=selector, value=value)

        # X/Y coordinate pairs (scroll_x/scroll_y, etc.)
        for x_field, y_field in self.XY_PAIRS.items():
            if x_field in action:
                template = self.TEMPLATES[x_field]
                x_val = action.get(x_field, 0)
                y_val = action.get(y_field, 0)
                return template.format(x=x_val, y=y_val)

        # Dropdown (needs both field_id and field_value)
        if "dropdown_field_id" in action:
            template = self.TEMPLATES["dropdown_field_id"]
            return template.format(
                selector=action["dropdown_field_id"],
                value=action.get("dropdown_field_value", ""),
            )

        # Wait selector (needs value + timeout)
        if "wait_selector" in action:
            template = self.TEMPLATES["wait_selector"]
            return template.format(
                value=action["wait_selector"],
                timeout=action.get("wait_timeout", 5000),
            )

        # evaluate_js gets repr() to safely quote the JS string
        if "evaluate_js" in action:
            template = self.TEMPLATES["evaluate_js"]
            return template.format(value=repr(action["evaluate_js"]))

        # All remaining single-value and zero-arg actions
        for field, template in self.TEMPLATES.items():
            if field in action:
                if "{value}" in template:
                    return template.format(value=action[field])
                return template

        return f"# Unrecognized action: {json.dumps(action)}"

    def generate_script(self):
        """
        Generates the full Playwright script from the sequence of actions and
        writes it to the output path.
        """
        actions_list = self._get_run_actions()

        # Derive the start URL from the first goto action if available
        start_url = "https://search.brave.com/"
        for action in actions_list:
            if "goto" in action:
                start_url = action["goto"]
                break

        script_header = (
            "import time\n"
            "from playwright.sync_api import sync_playwright\n\n"
            "def run_automation():\n"
            "    with sync_playwright() as p:\n"
            "        browser = p.chromium.launch(headless=False)\n"
            "        page = browser.new_page()\n\n"
            f"        page.goto('{start_url}')\n\n"
        )

        script_footer = (
            "        time.sleep(3)\n"
            "        browser.close()\n\n"
            "if __name__ == '__main__':\n"
            "    run_automation()\n"
        )

        script_body = []
        for action in actions_list:
            code = self._parse_action_to_code(action)
            indented_code = "        " + code.replace("\n", "\n        ")
            script_body.append(indented_code)
            script_body.append("")

        final_script = script_header + "\n".join(script_body) + script_footer

        try:
            with open(self.output_path, "w") as f:
                f.write(final_script)
        except Exception as e:
            self.log.error(f"Error writing script to file: {e}")
