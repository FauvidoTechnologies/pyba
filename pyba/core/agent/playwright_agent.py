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
        - `process_action`: for returning the right action on a page
        - `get_output`: for summarizing the chat and returning a string
    """

    def __init__(self, engine) -> None:
        """
        Args:
            `engine`: holds all the arguments from the user including the mode
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
        Method to initailise the main instruction for any agent

        Args:
            `cleaned_dom`: A dictionary containing nicely formatted DOM elements
            `user_prompt`: The instructions given by the user
            `main_instruction`: The prompt for the playwright agent
            `previous_action`: The previous action
            `fail_reason`: The reason for the failure of the previous action
            `action_status`: Boolean to decide if the previous action was a success or not

        TODO: Add `history` of ALL/SOME actions to give some context as to where we are headed

        # DEPRECATED - The fail_reason decides if the previous access was a success or not.

        For each run, a prompt containing the previous action, its status (success or failure) and a fail reason (if
        it failed) is provided. This helps the model reason better
        """

        # Adding the user_prompt to the DOM to make it easier to format the prompt
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
            `agent`: The agent to use (action_agent or output_agent)
            `prompt`: The fully formatted prompt string
            `agent_type`: "action" or "output", to determine parsing logic
            `cleaned_dom`: A dictionary that holds the `actual_text` from which the data is to be extracted
            `context_id`: A unique identifier for this browser window (useful when multiple windows)
            `extractor`: The extraction agent for this call (passed in to avoid shared mutable state)
            `user_prompt`: The original user prompt for this call (passed in to avoid shared mutable state)

        Returns:
            The parsed response (SimpleNamespace for action, str for output)
        """

        # If this guy gives me an output which says I need to extract the relevant data from this page,
        # Then I call the extraction agent here and extract information in a separate thread? Separate thread is easier,
        # I don't have to write my functions as async then

        if self.engine.provider == "openai":
            response = self.handle_openai_execution(
                agent=agent, prompt=prompt, context_id=context_id
            )
            parsed_json = json.loads(response.choices[0].message.content)

            # Parse based on agent type
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

                # Parse based on agent type
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
                # If we have a response which cannot be parsed, it MUST be a None value

        else:  # Using gemini
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
        Method to process the DOM and provide an actionable playwright response

        Args:
            `cleaned_dom`: Dictionary of the extracted items from the DOM
                - `hyperlinks`: List
                - `input_fields` (basically all fillable boxes): List
                - `clickable_fields`: List
                - `actual_text`: string
            `user_prompt`: The instructions given by the user
            `previous_action`: The previous executed action
            `fail_reason`: Holds the fail-reason should the previous task fail
            `extraction_format`: The extraction format for the task
            `context_id`: A unique identifier for this browser window (useful when multiple windows)
            `fail_reason`: The reason for failure of the previous action (None if not provided => Action passed)
            `action_status`: The success or the failure of an action

        output:
            A predefined pydantic model called `PlaywrightResponse` which defines our DSL
        """

        prompt = self._initialise_prompt(
            cleaned_dom=cleaned_dom,
            user_prompt=user_prompt,
            main_instruction=general_prompt,
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
        Method to get the final output from the model if the user requested for one
        """

        prompt = self._initialise_prompt(
            cleaned_dom=cleaned_dom, user_prompt=user_prompt, main_instruction=output_prompt
        )

        return self._call_model(
            agent=self.output_agent, prompt=prompt, agent_type="output", context_id=context_id
        )
