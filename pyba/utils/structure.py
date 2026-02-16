from dataclasses import dataclass, field
from typing import Optional, List, Dict

from pydantic import BaseModel, Field


class PlaywrightAction(BaseModel):
    goto: Optional[str] = Field(
        None,
        description="URL to navigate to. Provide a full URL including protocol.",
    )
    go_back: Optional[bool] = Field(
        None,
        description="Set true to go back one step in browser history, like clicking the back button.",
    )
    go_forward: Optional[bool] = Field(
        None,
        description="Set true to go forward one step in browser history.",
    )
    reload: Optional[bool] = Field(
        None,
        description="Set true to reload the current page.",
    )

    click: Optional[str] = Field(
        None,
        description="CSS selector of the element to single-click. Use for links, buttons, and interactive elements.",
    )
    dblclick: Optional[str] = Field(
        None,
        description="CSS selector of the element to double-click. Use for elements requiring double-click activation.",
    )
    hover: Optional[str] = Field(
        None,
        description="CSS selector of the element to hover over without clicking. Use to reveal tooltips or dropdown menus.",
    )
    right_click: Optional[str] = Field(
        None,
        description="CSS selector of the element to right-click. Use to open context menus.",
    )

    dropdown_field_id: Optional[str] = Field(
        None,
        description="CSS selector of a custom (non-native) dropdown menu. Must be paired with dropdown_field_value. Use for JavaScript-based dropdowns, NOT native <select> elements.",
    )
    dropdown_field_value: Optional[str] = Field(
        None,
        description="The visible text or value of the option to choose from the dropdown specified by dropdown_field_id.",
    )

    fill_selector: Optional[str] = Field(
        None,
        description="CSS selector of an input field to fill. Clears any existing text first, then sets the value. Must be paired with fill_value. Preferred over type_selector for most form inputs.",
    )
    fill_value: Optional[str] = Field(
        None,
        description="The text to insert into the input field specified by fill_selector.",
    )
    type_selector: Optional[str] = Field(
        None,
        description="CSS selector of an input field to type into character-by-character. Fires individual keystroke events, which can trigger autocomplete or live search. Must be paired with type_text. Use instead of fill when keystroke events matter.",
    )
    type_text: Optional[str] = Field(
        None,
        description="The text to type character-by-character into the element specified by type_selector.",
    )
    press_selector: Optional[str] = Field(
        None,
        description="CSS selector of the element to send a keypress to. Must be paired with press_key. Use to submit forms or trigger keyboard shortcuts on a specific element.",
    )
    press_key: Optional[str] = Field(
        None,
        description="Name of the key to press on the element specified by press_selector. Examples: 'Enter', 'Escape', 'Tab', 'ArrowDown', 'Backspace'.",
    )
    check: Optional[str] = Field(
        None,
        description="CSS selector of a checkbox or radio button to mark as checked.",
    )
    uncheck: Optional[str] = Field(
        None,
        description="CSS selector of a checkbox to mark as unchecked.",
    )
    select_selector: Optional[str] = Field(
        None,
        description="CSS selector of a native HTML <select> dropdown. Must be paired with select_value. Use for native <select> elements, NOT custom JavaScript dropdowns.",
    )
    select_value: Optional[str] = Field(
        None,
        description="The option value to pick from the native <select> element specified by select_selector.",
    )
    upload_selector: Optional[str] = Field(
        None,
        description="CSS selector of a file input element (<input type='file'>). Must be paired with upload_path.",
    )
    upload_path: Optional[str] = Field(
        None,
        description="Absolute file path to upload into the file input specified by upload_selector.",
    )

    scroll_x: Optional[int] = Field(
        None,
        description="Horizontal pixel position to scroll to. 0 is the left edge. Must be paired with scroll_y.",
    )
    scroll_y: Optional[int] = Field(
        None,
        description="Vertical pixel position to scroll to. 0 is the top. Use to reveal content below the current viewport. Must be paired with scroll_x.",
    )
    wait_selector: Optional[str] = Field(
        None,
        description="CSS selector to wait for before proceeding. Use when content loads asynchronously after a navigation or action.",
    )
    wait_timeout: Optional[int] = Field(
        None,
        description="Maximum time in milliseconds to wait for wait_selector to appear. Only meaningful alongside wait_selector.",
    )
    wait_ms: Optional[int] = Field(
        None,
        description="Fixed pause in milliseconds. Use for waiting on animations, transitions, or delays with no specific selector to wait for.",
    )

    keyboard_press: Optional[str] = Field(
        None,
        description="Key to press globally without targeting a specific element. Acts on whatever is currently focused. Examples: 'Enter', 'Escape', 'Tab'. Differs from press_selector+press_key which targets a specific element.",
    )
    keyboard_type: Optional[str] = Field(
        None,
        description="Text to type globally into whatever element is currently focused. Differs from type_selector+type_text which targets a specific element.",
    )
    mouse_move_x: Optional[int] = Field(
        None,
        description="X pixel coordinate to move the mouse cursor to. Must be paired with mouse_move_y.",
    )
    mouse_move_y: Optional[int] = Field(
        None,
        description="Y pixel coordinate to move the mouse cursor to. Must be paired with mouse_move_x.",
    )
    mouse_click_x: Optional[int] = Field(
        None,
        description="X pixel coordinate for a direct mouse click. Must be paired with mouse_click_y. Use as a fallback when no CSS selector is available for the target element.",
    )
    mouse_click_y: Optional[int] = Field(
        None,
        description="Y pixel coordinate for a direct mouse click. Must be paired with mouse_click_x.",
    )

    new_page: Optional[str] = Field(
        None,
        description="URL to open in a new browser tab. Pass an empty string to open a blank tab.",
    )
    close_page: Optional[bool] = Field(
        None,
        description="Set true to close the current browser tab.",
    )
    switch_page_index: Optional[int] = Field(
        None,
        description="Zero-based index of the browser tab to switch to. 0 is the first tab.",
    )

    evaluate_js: Optional[str] = Field(
        None,
        description="JavaScript code to execute in the page context. Use as a last resort when no standard action fits the need.",
    )
    screenshot_path: Optional[str] = Field(
        None,
        description="File path to save a screenshot of the current page state.",
    )
    download_selector: Optional[str] = Field(
        None,
        description="CSS selector of a link or button that triggers a file download when clicked.",
    )


class PlaywrightResponse(BaseModel):
    actions: List[PlaywrightAction]
    extract_info: Optional[bool] = Field(
        ...,
        description="Set true if the current page contains data the user requested and extraction should run. Set false otherwise. Never extract content yourself.",
    )


class OutputResponseFormat(BaseModel):
    output: str


@dataclass
class CleanedDOM:
    """
    Represents the cleaned DOM snapshot of the current browser page.

    Additional parameter for the youtube DOM extraction
    """

    hyperlinks: Optional[List[str]] = field(default_factory=list)
    input_fields: Optional[List[str]] = field(default_factory=list)
    clickable_fields: Optional[List[str]] = field(default_factory=list)
    actual_text: Optional[str] = None
    current_url: Optional[str] = None
    youtube: Optional[str] = None  # For YouTube based DOM extraction

    def to_dict(self) -> dict:
        return {
            "hyperlinks": self.hyperlinks,
            "input_fields": self.input_fields,
            "clickable_fields": self.clickable_fields,
            "actual_text": self.actual_text,
            "current_url": self.current_url,
            "youtube": self.youtube,
        }


class PlannerAgentOutputBFS(BaseModel):
    plans: List[str] = Field(
        ...,
        description="List of independent exploration plans to execute in parallel. Each plan is a self-contained sequence of steps.",
    )


class PlannerAgentOutputDFS(BaseModel):
    plan: str = Field(
        ...,
        description="A single sequential plan to execute depth-first. Each step builds on the previous one.",
    )


class GeneralExtractionResponse(BaseModel):
    imp_visible_text: str = Field(
        ...,
        description="The relevant visible text from the page that matches the user's extraction request. Exclude navigation, ads, and boilerplate.",
    )
    general_dict: Optional[Dict[str, str]] = Field(
        ...,
        description="Key-value pairs of extracted data when structured output is more appropriate than plain text.",
    )
