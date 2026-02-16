import json
import threading

from pydantic import BaseModel

from pyba.core.agent.base_agent import BaseAgent
from pyba.utils.prompts.extraction_prompts import extraction_general_instruction


class ExtractionAgent(BaseAgent):
    """
    Handles structured data extraction from page content in a separate thread
    so it does not block the main automation pipeline.

    Args:
        extraction_format: Pydantic model defining the expected extraction output schema.
    """

    def __init__(self, engine, extraction_format: BaseModel):
        super().__init__(engine=engine)
        self.extraction_format = extraction_format
        self.agent = self.llm_factory.get_extraction_agent(
            extraction_format=self.extraction_format
        )

    def _initialise_prompt(self, task: str, actual_text: str):
        """
        Formats the extraction prompt with the user task and page text.

        Args:
            task: The user's extraction request.
            actual_text: The visible text content of the current page.
        """
        return extraction_general_instruction.format(task=task, actual_text=actual_text)

    def info_extraction(self, task: str, actual_text: str, context_id: str = None) -> None:
        """
        Function to extract data from the current page

        Args:
            task: The user's defined task
            actual_text: The current page text
            context_id: A unique identifier for this browser window (useful when multiple windows)

        Extracts data and logs it. Pushes to semantic memory if a database is configured.
        """
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
                self.log.error(f"Unable to parse the output from OpenAI response: {e}")
                return None
        elif self.engine.provider == "vertexai":
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
                    self.engine.db_funcs.push_to_semantic_memory(
                        self.engine.session_id, logs=parsed_object.json()
                    )
                    self.log.info("Added to semantic memory")

            except Exception as e:
                if not response:
                    self.log.error(f"Unable to parse the output from VertexAI response: {e}")
        else:
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
        Runs info_extraction in a daemon thread so extraction does not block the main loop.

        Args:
            task: The user's extraction request.
            actual_text: The visible text content of the current page.
        """
        self.log.info("Running the extractor on the current page")
        thread = threading.Thread(
            target=self.info_extraction,
            args=(task, actual_text),
            daemon=True,
        )
        thread.start()
