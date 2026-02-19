_general = """
## Task
{user_prompt}

## Current Page

URL: {current_url}

Hyperlinks:
{hyperlinks}

Input Fields:
{input_fields}

Clickable Elements:
{clickable_fields}

Visible Text:
{actual_text}

## Full Action History

Below is the complete sequence of actions taken so far in this session. Each entry shows the step number, whether it succeeded or failed (with failure reason if applicable), and a description of what was done. Use this history to understand what has already been attempted, avoid repeating failed approaches, and determine the best next action.

{action_history}
"""

general_prompt = {
    "openai": _general,
    "vertexai": _general,
    "gemini": _general,
}
