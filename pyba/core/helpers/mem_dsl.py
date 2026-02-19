class MemDSL:
    """
    Deterministic converter from raw PlaywrightAction objects to natural language
    summaries. Accumulates every action into a rolling history string that gets
    injected into the LLM prompt, giving the model full session context.

    The dispatch order mirrors PlaywrightActionPerformer.perform() exactly so
    that priority semantics stay consistent between execution and logging.
    """

    def __init__(self):
        self._steps = []
        self._step_count = 0

    def record(self, action, success: bool, fail_reason=None) -> str:
        """
        Converts an action and its outcome into a natural language line,
        appends it to the internal history, and returns the line.

        The returned line doubles as the message for Logger.action().

        Args:
                action: A PlaywrightAction (Pydantic) or SimpleNamespace with the same fields
                success: Whether the action executed without raising an exception
                fail_reason: The exception or error string when success is False
        """
        self._step_count += 1
        message = self._resolve(action)

        if success:
            line = f"Step {self._step_count} [OK]: {message}"
        else:
            line = f"Step {self._step_count} [FAILED]: {message}. Failure reason: {fail_reason}"

        self._steps.append(line)
        return line

    @property
    def history(self) -> str:
        """The full accumulated history string ready for prompt injection."""
        return "\n".join(self._steps)

    def _resolve(self, action) -> str:
        """
        Pattern-matches on which fields are set in the action and returns
        the corresponding natural language description.

        Uses getattr for safety across both Pydantic models and SimpleNamespace.
        """

        def g(field):
            return getattr(action, field, None)

        # --- Navigation ---

        if g("goto"):
            return f"Navigated the browser to {g('goto')}"
        if g("go_back"):
            return "Went back to the previous page in browser history"
        if g("go_forward"):
            return "Went forward to the next page in browser history"
        if g("reload"):
            return "Reloaded the current page"

        # --- Form input ---

        if g("fill_selector") and g("fill_value") is not None:
            return (
                f"Cleared and filled the input field '{g('fill_selector')}' "
                f"with the text '{g('fill_value')}'"
            )
        if g("type_selector") and g("type_text"):
            return (
                f"Typed '{g('type_text')}' character by character "
                f"into the input field '{g('type_selector')}'"
            )

        # --- Click variants ---

        if g("click"):
            return f"Clicked on the element '{g('click')}' on the page"
        if g("dblclick"):
            return f"Double-clicked the element '{g('dblclick')}' on the page"
        if g("dropdown_field_id"):
            return (
                f"Selected the option '{g('dropdown_field_value')}' "
                f"from the custom dropdown '{g('dropdown_field_id')}'"
            )
        if g("right_click"):
            return f"Right-clicked on the element '{g('right_click')}' to open context menu"
        if g("hover"):
            return f"Hovered over the element '{g('hover')}' without clicking"

        # --- Press / keyboard ---

        if g("press_selector") or g("press_key"):
            if g("press_selector") and g("press_key"):
                return f"Pressed the '{g('press_key')}' key on the element '{g('press_selector')}'"
            return f"Pressed the '{g('press_key')}' key on the currently focused element"
        if g("keyboard_press"):
            return f"Pressed the '{g('keyboard_press')}' key on the currently focused element"
        if g("keyboard_type"):
            return f"Typed the text '{g('keyboard_type')}' into the currently focused element"

        # --- Checkboxes ---

        if g("check"):
            return f"Checked the checkbox '{g('check')}'"
        if g("uncheck"):
            return f"Unchecked the checkbox '{g('uncheck')}'"

        # --- Select / upload ---

        if g("select_selector") and g("select_value"):
            return (
                f"Selected the option '{g('select_value')}' "
                f"from the native dropdown '{g('select_selector')}'"
            )
        if g("upload_selector") and g("upload_path"):
            return (
                f"Uploaded the file '{g('upload_path')}' "
                f"using the file input '{g('upload_selector')}'"
            )

        # --- Scroll ---

        if g("scroll_x") or g("scroll_y"):
            x = g("scroll_x") or 0
            y = g("scroll_y") or 0
            return f"Scrolled the page to horizontal position {x} and vertical position {y}"

        # --- Wait ---

        if g("wait_selector") or g("wait_ms"):
            if g("wait_selector"):
                timeout = g("wait_timeout")
                if timeout:
                    return (
                        f"Waited for the element '{g('wait_selector')}' to appear "
                        f"on the page with a timeout of {timeout}ms"
                    )
                return f"Waited for the element '{g('wait_selector')}' to appear on the page"
            return f"Paused execution for {g('wait_ms')} milliseconds"

        # --- JavaScript / screenshot / download ---

        if g("evaluate_js"):
            return "Executed custom JavaScript on the page"
        if g("screenshot_path"):
            return f"Captured a screenshot of the page and saved it to '{g('screenshot_path')}'"
        if g("download_selector"):
            return f"Initiated a file download by clicking on '{g('download_selector')}'"

        # --- Tab management ---

        if g("new_page"):
            return f"Opened a new browser tab and navigated it to {g('new_page')}"
        if g("close_page"):
            return "Closed the currently active browser tab"
        if g("switch_page_index") is not None:
            return f"Switched to browser tab number {g('switch_page_index')}"

        # --- Mouse (direct coordinate actions) ---

        if g("mouse_move_x") is not None or g("mouse_move_y") is not None:
            x = g("mouse_move_x") or 0
            y = g("mouse_move_y") or 0
            return f"Moved the mouse cursor to coordinates ({x}, {y}) on the page"
        if g("mouse_click_x") is not None or g("mouse_click_y") is not None:
            x = g("mouse_click_x") or 0
            y = g("mouse_click_y") or 0
            return f"Performed a direct mouse click at coordinates ({x}, {y}) on the page"

        return "Performed an unrecognized action"
