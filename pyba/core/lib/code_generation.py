import json
import re
from typing import List

from pyba.database import DatabaseFunctions


class CodeGeneration:
    """
    Create the full automation code used by the model

    - Requires the database to be populated with all the actions
    - Pulls action from the database and writes the script at a user location

    Args:
            `session_id`: The unique idenfier for this session
            `output_path`: Path to save the code to
            `database_funcs`: The Database instantiated by the user

    Probably rewritten a lot of the code I already have from the dispatcher. There must be a simpler way
    TODO: Clean up
    """

    def __init__(self, session_id: str, output_path: str, database_funcs: DatabaseFunctions):
        self.session_id = session_id
        self.output_path = output_path
        self.db_funcs = database_funcs

        # Mapping of action fields to their corresponding Playwright code method and format
        # The format string uses {selector} and {value} placeholders
        # For actions involving both selector and value, both are expected.
        # For navigation/single-value actions, only the value is used (as {value}).
        self.action_map = {
            "goto": (
                'page.goto("{value}")',
                1,
            ),  # (code_template, num_args: 1 for value, 2 for selector/value)
            "go_back": ("page.go_back()", 0),
            "go_forward": ("page.go_forward()", 0),
            "reload": ("page.reload()", 0),
            "click": ('page.click("{value}")', 1),
            "dblclick": ('page.dblclick("{value}")', 1),
            "hover": ('page.hover("{value}")', 1),
            "fill_selector": ('page.fill("{selector}", "{value}")', 2),  # Uses fill_value
            "type_selector": ('page.type("{selector}", "{value}")', 2),  # Uses type_text
            "press_selector": ('page.press("{selector}", "{value}")', 2),  # Uses press_key
            "check": ('page.check("{value}")', 1),
            "uncheck": ('page.uncheck("{value}")', 1),
            "select_selector": (
                'page.select_option("{selector}", "{value}")',
                2,
            ),  # Uses select_value
            "upload_selector": (
                'page.set_input_files("{selector}", "{value}")',
                2,
            ),  # Uses upload_path
            "scroll_x": (
                "page.mouse.wheel({value_x}, {value_y})",
                2,
                "scroll_y",
            ),  # Special handling in _parse_action_to_code
            "wait_selector": (
                'page.wait_for_selector("{value}", timeout={value_timeout})',
                2,
                "wait_timeout",
            ),  # Special handling
            "wait_ms": ("page.wait_for_timeout({value})", 1),  # Uses wait_ms
            "keyboard_press": ('page.keyboard.press("{value}")', 1),
            "keyboard_type": ('page.keyboard.type("{value}")', 1),
            "mouse_move_x": (
                "page.mouse.move({value_x}, {value_y})",
                2,
                "mouse_move_y",
            ),  # Special handling
            "mouse_click_x": (
                "page.mouse.click({value_x}, {value_y})",
                2,
                "mouse_click_y",
            ),  # Special handling
            # New pages/context actions are generally harder to script simply; using basic page-level equivalent
            "screenshot_path": ('page.screenshot(path="{value}")', 1),
            "evaluate_js": ('page.evaluate("{value}")', 1),
            "download_selector": (
                'with page.expect_download() as download_info:\n    page.click("{value}")\ndownload = download_info.value\ndownload.save_as(download.suggested_filename)',
                1,
            ),
            "new_page": (
                '# NOTE: Creating new pages is complex in a simple script\npage.context.new_page().goto("{value}")',
                1,
            ),  # Simplified, not strictly correct for current page state
            "close_page": ("page.close()", 0),
            "switch_page_index": (
                "# NOTE: Page switching is context-dependent\npage = page.context.pages[{value}]",
                1,
            ),  # Simplified assumption
        }

    def _get_run_actions(self) -> List:
        """
        Function to query the database and get the stack of all actions
        that have been performed up to the time the function was called
        """

        logs = self.db_funcs.get_episodic_memory_by_session_id(session_id=self.session_id)

        if logs and logs.actions:
            actions_list = json.loads(logs.actions)
            return actions_list
        return []

    def _parse_action_to_code(self, action_str: str) -> str:
        """
        Converts a single action string (e.g., 'goto="url" fill_selector=None...')
        into a Playwright code string.
        """
        # The first step is to parse the action string into a dictionary of key-value pairs
        # This pattern is robust to handle both 'key=value' and 'key="value"'
        action_data = {}

        # Replace quoted strings with a placeholder to avoid splitting on commas inside the value
        # A simpler approach given the specific format is to split by spaces and then by '='
        # The initial format of the action string is: key1=value1 key2=value2 ...
        parts = re.findall(r"(\w+)=([^ ]*)", action_str)

        for key, value in parts:
            # Strip quotes/None/None-like strings
            cleaned_value = value.strip().strip("'\"")
            if cleaned_value.lower() not in ("none", "false", ""):
                action_data[key] = cleaned_value

        code_lines = []

        # Check the action_map keys to find the one that is present (not None) in action_data
        for action_field, (template, num_args, *extra_field) in self.action_map.items():
            if action_field in action_data:
                # Navigation actions (e.g., go_back, reload)
                if num_args == 0:
                    code_lines.append(template)
                    break  # Assuming only one action per step right now

                elif num_args == 1:
                    if action_field == "download_selector":
                        code = template.replace('"{value}"', f'"{action_data[action_field]}"')
                        code_lines.extend(code.split("\n"))
                    else:
                        # Simple template replacement
                        code = template.format(value=action_data[action_field])
                        code_lines.append(code)
                    break

                # Two-argument actions (e.g., fill_selector/fill_value, scroll_x/scroll_y)
                elif num_args == 2:
                    # 1. Selector/Value pairs (e.g., fill_selector/fill_value, type_selector/type_text)
                    if action_field.endswith("_selector") or action_field == "wait_selector":
                        # Determine the corresponding value field
                        if action_field == "fill_selector":
                            value_field = "fill_value"
                        elif action_field == "type_selector":
                            value_field = "type_text"
                        elif action_field == "press_selector":
                            value_field = "press_key"
                        elif action_field == "select_selector":
                            value_field = "select_value"
                        elif action_field == "upload_selector":
                            value_field = "upload_path"
                        elif action_field == "wait_selector":
                            value_field = "wait_timeout"
                        else:
                            continue  # Should not happen

                        selector = action_data.get(action_field)
                        value = action_data.get(value_field)

                        if selector and value is not None:
                            # Handlin special case for wait_selector and wait_timeout
                            if action_field == "wait_selector" and "wait_timeout" in action_data:
                                timeout = action_data["wait_timeout"]
                                code = template.format(value=selector, value_timeout=timeout)
                            # Handling special case for fill_value being an empty string (is still a valid action)
                            elif (
                                action_field == "fill_selector"
                                and action_data.get("fill_value") == ""
                            ):
                                code = template.format(selector=selector, value="")
                            else:
                                code = template.format(selector=selector, value=value)

                            code_lines.append(code)
                            break

                    # 2. X/Y pairs (e.g., scroll_x/scroll_y)
                    elif (
                        action_field.endswith("_x")
                        and extra_field
                        and extra_field[0].endswith("_y")
                    ):
                        y_field = extra_field[0]
                        x_val = action_data.get(action_field)
                        y_val = action_data.get(y_field)

                        if x_val is not None or y_val is not None:
                            # Default to 0 if the other is None, as per Playwright
                            x_val = x_val if x_val is not None else 0
                            y_val = y_val if y_val is not None else 0

                            code = template.format(value_x=x_val, value_y=y_val)
                            code_lines.append(code)
                            break

        return (
            "\n".join(code_lines)
            if code_lines
            else f"# Action not supported or complete: {action_str}"
        )

    def generate_script(self):
        """
        Generates the full Playwright script from the sequence of actions and
        writes it to the output path.
        """

        actions_list = self._get_run_actions()

        # Boilerplate
        script_header = (
            "import time\n"
            "from playwright.sync_api import sync_playwright\n\n"
            "def run_automation():\n"
            "    with sync_playwright() as p:\n"
            "        browser = p.chromium.launch(headless=False)\n"
            "        page = browser.new_page()\n\n"
            "        page.goto('https://search.brave.com/')\n\n"
        )

        script_footer = (
            "        time.sleep(3) # Keep browser open for 3 seconds to see the result\n"
            "        browser.close()\n\n"
            "if __name__ == '__main__':\n"
            "    run_automation()\n"
        )

        script_body = []

        for i, action_str in enumerate(actions_list):
            code = self._parse_action_to_code(action_str)

            indented_code = "        " + code.replace("\n", "\n        ")

            script_body.append(indented_code)
            script_body.append("")  # Empty line for separation

        final_script = script_header + "\n".join(script_body) + script_footer

        try:
            with open(self.output_path, "w") as f:
                f.write(final_script)
        except Exception as e:
            print(f"Error writing script to file: {e}")
