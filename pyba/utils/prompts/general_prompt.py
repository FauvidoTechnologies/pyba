_stateless = """
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

## Previous Step

Action: {previous_action}
Succeeded: {action_status}
Failure reason: {fail_reason}
"""

_stateful = """
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

## Last Action Result

Succeeded: {action_status}
Failure reason: {fail_reason}
"""

general_prompt = {
    "openai": _stateless,
    "vertexai": _stateful,
    "gemini": _stateless,
}
