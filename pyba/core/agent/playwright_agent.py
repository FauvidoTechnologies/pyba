import json
from types import SimpleNamespace
from typing import Dict, List, Union, Any

from pydantic import BaseModel

from pyba.core.agent.base_agent import BaseAgent
from pyba.core.agent.extraction_agent import ExtractionAgent
from pyba.utils.prompts import general_prompt, output_prompt
from pyba.utils.structure import PlaywrightResponse


class PlaywrightAgent(BaseAgent):
    """
    Defines the playwright agent's actions

    Provides two endpoints:
        - process_action: for returning the right action on a page
        - get_output: for summarizing the chat and returning a string
    """

    def __init__(self, engine) -> None:
        """
        Args:
            engine: holds all the arguments from the user including the mode
        """
        super().__init__(engine=engine)  # Initialising the base params from BaseAgent
        self.action_agent, self.output_agent = self.llm_factory.get_agent()

    def _initialise_prompt(
        self,
        cleaned_dom: Dict[str, Union[List, str]],
        user_prompt: str,
        main_instruction: str,
        previous_action: str = None,
        fail_reason: str = None,
        action_status: bool = None,
    ):
        """
        Formats the prompt template by injecting DOM data and action context.

        Args:
            cleaned_dom: Dictionary of extracted DOM elements.
            user_prompt: The user's task instruction.
            main_instruction: The prompt template to format.
            previous_action: Serialised previous action.
            fail_reason: Reason the previous action failed, if applicable.
            action_status: Whether the previous action succeeded.
        """

        cleaned_dom["user_prompt"] = user_prompt
        cleaned_dom["previous_action"] = previous_action
        cleaned_dom["action_status"] = action_status
        cleaned_dom["fail_reason"] = fail_reason

        prompt = main_instruction.format(**cleaned_dom)

        return prompt

    def _call_model(
        self,
        agent: Any,
        prompt: str,
        agent_type: str,
        cleaned_dom: Dict = None,
        context_id: str = None,
        extractor=None,
        user_prompt: str = None,
    ) -> Any:
        """
        Generic method to call the correct LLM provider and parse the response.

        Args:
            agent: The agent to use (action_agent or output_agent)
            prompt: The fully formatted prompt string
            agent_type: "action" or "output", to determine parsing logic
            cleaned_dom: A dictionary that holds the `actual_text` from which the data is to be extracted
            context_id: A unique identifier for this browser window (useful when multiple windows)
            extractor: The extraction agent for this call (passed in to avoid shared mutable state)
            user_prompt: The original user prompt for this call (passed in to avoid shared mutable state)

        Returns:
            The parsed response (SimpleNamespace for action, str for output)
        """

        if self.engine.provider == "openai":
            response = self.handle_openai_execution(
                agent=agent, prompt=prompt, context_id=context_id
            )
            parsed_json = json.loads(response.choices[0].message.content)

            if agent_type == "action":
                actions = SimpleNamespace(**parsed_json.get("actions")[0])
                extract_info_flag = parsed_json.get("extract_info")
                if extract_info_flag:
                    extractor.run_threaded_info_extraction(
                        task=user_prompt, actual_text=cleaned_dom["actual_text"]
                    )
                return actions
            elif agent_type == "output":
                return str(parsed_json.get("output"))

        elif self.engine.provider == "vertexai":  # VertexAI logic
            response = self.handle_vertexai_execution(
                agent=agent, prompt=prompt, context_id=context_id
            )
            try:
                parsed_object = getattr(
                    response, "output_parsed", getattr(response, "parsed", None)
                )

                if not parsed_object:
                    self.log.error("No parsed object found in VertexAI response.")
                    return None

                if agent_type == "action":
                    if hasattr(parsed_object, "actions") and parsed_object.actions:
                        actions = parsed_object.actions[0]
                        extract_info_flag = parsed_object.extract_info
                        if extract_info_flag:
                            extractor.run_threaded_info_extraction(
                                task=user_prompt, actual_text=cleaned_dom["actual_text"]
                            )
                        return actions
                    raise IndexError("No 'actions' found in VertexAI response.")
                elif agent_type == "output":
                    if hasattr(parsed_object, "output") and parsed_object.output:
                        return str(parsed_object.output)
                    raise IndexError("No 'output' found in VertexAI response.")

            except Exception as e:
                if not response:
                    self.log.error(f"Unable to parse the output from VertexAI response: {e}")
        else:
            response = self.handle_gemini_execution(
                agent=agent, prompt=prompt, context_id=context_id
            )
            parsed_object = agent["response_format"].model_validate_json(response.text)
            if agent_type == "action":
                if parsed_object.actions:
                    actions = parsed_object.actions[0]
                    extract_info_flag = parsed_object.extract_info
                    if extract_info_flag:
                        extractor.run_threaded_info_extraction(
                            task=user_prompt, actual_text=cleaned_dom["actual_text"]
                        )
                    return actions
            elif agent_type == "output":
                return str(parsed_object.output)

    def process_action(
        self,
        cleaned_dom: Dict[str, Union[List, str]],
        user_prompt: str,
        previous_action: str = None,
        fail_reason: str = None,
        extraction_format: BaseModel = None,
        context_id: str = None,
        action_status: bool = None,
    ) -> PlaywrightResponse:
        """
        Processes the current DOM and returns the next PlaywrightAction to execute.

        Args:
            cleaned_dom: Dictionary of extracted DOM elements (hyperlinks, input_fields, clickable_fields, actual_text).
            user_prompt: The user's task instruction.
            previous_action: Serialised previous action.
            fail_reason: Reason the previous action failed, if applicable.
            extraction_format: Pydantic model defining the extraction output schema.
            context_id: Unique identifier for this browser window (used in BFS mode).
            action_status: Whether the previous action succeeded.

        Returns:
            A PlaywrightAction to execute next, or None if the task is complete.
        """

        prompt = self._initialise_prompt(
            cleaned_dom=cleaned_dom,
            user_prompt=user_prompt,
            main_instruction=general_prompt[self.engine.provider],
            previous_action=previous_action if previous_action else "",
            fail_reason=fail_reason if fail_reason else "",
            action_status=action_status if action_status else "",
        )

        extractor = ExtractionAgent(engine=self.engine, extraction_format=extraction_format)

        return self._call_model(
            agent=self.action_agent,
            prompt=prompt,
            agent_type="action",
            cleaned_dom=cleaned_dom,
            context_id=context_id,
            extractor=extractor,
            user_prompt=user_prompt,
        )

    def get_output(
        self, cleaned_dom: Dict[str, Union[List, str]], user_prompt: str, context_id: str = None
    ) -> str:
        """
        Gets the final text output from the model based on the current page state.
        """

        prompt = self._initialise_prompt(
            cleaned_dom=cleaned_dom, user_prompt=user_prompt, main_instruction=output_prompt
        )

        return self._call_model(
            agent=self.output_agent, prompt=prompt, agent_type="output", context_id=context_id
        )
