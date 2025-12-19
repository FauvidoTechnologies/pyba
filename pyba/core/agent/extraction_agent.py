import json
import threading

from pydantic import BaseModel

from pyba.core.agent.base_agent import BaseAgent
from pyba.utils.prompts.extraction_prompts import extraction_general_instruction


class ExtractionAgent(BaseAgent):
    """
    This is a helper agent in all aspects. To use this, all other agents
    need to import and initialise this.

    This agent allows for threaded infomation extraction to not hinder the main pipeline flow.

    Args:
        `extraction_format`: The format which should be fitted for the extraction
    """

    def __init__(self, engine, extraction_format: BaseModel):
        super().__init__(engine=engine)  # Initialising the base params from BaseAgent

        self.extraction_format = extraction_format
        self.agent = self.llm_factory.get_extraction_agent(
            extraction_format=self.extraction_format
        )  # Getting the extraction agent

    def _initialise_prompt(self, task: str, actual_text: str):
        """
        Takes in the actual_text and wraps it around the general prompt

        Args:
                `task`: The user's defined task
                `actual_text`: The current text on the page
        """
        return extraction_general_instruction.format(task=task, actual_text=actual_text)

    def info_extraction(self, task: str, actual_text: str, context_id: str = None) -> None:
        """
        Function to extract data from the current page

        Args:
            `task`: The user's defined task
            `actual_text`: The current page text
            `context_id`: A unique identifier for this browser window (useful when multiple windows)

        This function for now only Logs the value and doesn't return anything
        """

        # THE FINAL PIECE OF THE PUZZLE
        prompt = self._initialise_prompt(task=task, actual_text=actual_text)

        if self.engine.provider == "openai":
            response = self.handle_openai_execution(
                agent=self.agent,
                prompt=prompt,
                context_id=context_id,
            )
            try:
                parsed_json = json.loads(response.choices[0].message.content)
                self.log.info(f"Extracted content: {parsed_json}")
                if self.engine.db_funcs:
                    self.engine.db_funcs.push_to_semantic_memory(
                        self.engine.session_id, logs=json.dumps(parsed_json)
                    )
                    self.log.info("Added to semantic memory")
            except Exception as e:
                self.log.error(f"Unable to parse the outoput from OpenAI response: {e}")
                return None
        elif self.engine.provider == "vertexai":
            print("In here")
            response = self.handle_vertexai_execution(
                agent=self.agent, prompt=prompt, context_id=context_id
            )

            try:
                parsed_object = getattr(
                    response, "output_parsed", getattr(response, "parsed", None)
                )

                if not parsed_object:
                    self.log.error("No parsed object found in VertexAI response.")
                    return None

                self.log.info(f"Extracted content: {parsed_object}")
                if self.engine.db_funcs:
                    print("in here")
                    self.engine.db_funcs.push_to_semantic_memory(
                        self.engine.session_id, logs=parsed_object.json()
                    )
                    self.log.info("Added to semantic memory")

            except Exception as e:
                print(f"hit exception: {e}")
                if not response:
                    self.log.error(f"Unable to parse the output from VertexAI response: {e}")
                # If we have a response which cannot be parsed, it MUST be a None value
        else:  # Using gemini
            response = self.handle_gemini_execution(
                agent=self.agent, prompt=prompt, context_id=context_id
            )
            parsed_object = self.agent["response_format"].model_validate_json(response.text)
            self.log.info(f"Extracted content: {parsed_object}")
            if self.engine.db_funcs:
                self.engine.db_funcs.push_to_semantic_memory(
                    self.engine.session_id, logs=parsed_object.json()
                )
                self.log.info("Added to semantic memory")

    def run_threaded_info_extraction(self, task: str, actual_text: str):
        """
                Fuction to thread the execution of the `info_extraction` function

                Args:
            `task`: The user's defined task
            `actual_text`: The current page text

        This function creates a separate thread for calling the agent on the current page
        and extracting the relevant information with the right format.
        """
        self.log.info("Running the extractor on the current page")
        thread = threading.Thread(
            target=self.info_extraction,
            args=(task, actual_text),
            daemon=True,
        )
        thread.start()
