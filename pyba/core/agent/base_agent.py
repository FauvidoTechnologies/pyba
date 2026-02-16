import random
import time
from typing import Literal, Dict, List, Any

from pyba.core.agent.llm_factory import LLMFactory
from pyba.logger import get_logger


class BaseAgent:
    """
    Base class for all agents. Provides LLM execution with exponential backoff
    and retry logic. The backoff is blocking per context to avoid overwhelming
    rate-limited APIs.

    Defines the following variables:

    exponential_base: 2 (we're using base 2)
    base_timeout: 1 second
    max_backoff_time: 60 seconds
    attempt_number: The current attempt number initialised to 1
    LLMFactory: The internal agent call is made by agent itself
    log: The logger for the agents
    """

    def __init__(self, engine):
        self.base = 2
        self.base_timeout = 1
        self.max_backoff_time = 60

        self.engine = engine
        self.llm_factory = LLMFactory(engine=self.engine)
        self.log = get_logger()
        self.mode: Literal["Normal", "DFS", "BFS"] = self.engine.mode
        self.shared_depth_dictionary = {}

    def _initialise_prompt(self):
        """
        Initialises the prompt. Must be implemented by each subclass.
        """
        raise NotImplementedError("Subclasses must implement _initialise_prompt")

    def _initialise_openai_arguments(
        self, system_instruction: str, prompt: str, model_name: str
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Initialises the arguments for OpenAI agents

        Args:
            system_instruction: The system instruction for the agent
            prompt: The current prompt for the agent
            model_name: The OpenAI model name

        Returns:
            An arguments dictionary which can be directly passed to OpenAI agents
        """

        messages = [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt},
        ]

        kwargs = {
            "model": model_name,
            "messages": messages,
        }

        return kwargs

    def handle_openai_execution(self, agent: Any, prompt: str, context_id: str = None):
        """
        Helper method to handle OpenAI execution

        Args:
            agent: The agent to use (action_agent or output_agent)
            prompt: The fully formatted prompt string
            context_id: A unique identifier for the current browser window

        The `context_id` is to help in differentiating between different browser windows during parallel execution
        for BFS mode.

        `context_id`=None => There is only one browser session.

        Returns:
            response: The raw response from the model. The exact required values
            are expected to be extracted within each agent.
        """
        arguments = self._initialise_openai_arguments(
            system_instruction=agent["system_instruction"],
            prompt=prompt,
            model_name=agent["model"],
        )

        while True:
            try:
                response = agent["client"].chat.completions.parse(
                    **arguments, response_format=agent["response_format"]
                )
                self.initialise_depth_ladder(unique_context_id=context_id)
                break
            except Exception:
                wait_time = self.calculate_next_time(
                    self.shared_depth_dictionary.get(context_id, 1)
                )
                self.log.warning(f"Hit the rate limit for OpenAI, retrying in {wait_time} seconds")
                time.sleep(wait_time)
                self.update_depth_ladder(unique_context_id=context_id)

        return response

    def handle_vertexai_execution(self, agent: Any, prompt: str, context_id: str = None):
        """
        Helper method to handle VertexAI execution

        Args:
            agent: The agent to use (action_agent or output_agent)
            prompt: The fully formatted prompt string
            context_id: A unique identifier for the current browser window

        The `context_id` is to help in differentiating between different browser windows during parallel execution
        for BFS mode.

        `context_id`=None => There is only one browser session.


        Returns:
            response: The raw response from the model. The exact required values
            are expected to be extracted within each agent.
        """
        while True:
            try:
                response = agent.send_message(prompt)
                self.initialise_depth_ladder(unique_context_id=context_id)
                break
            except Exception:
                wait_time = self.calculate_next_time(
                    self.shared_depth_dictionary.get(context_id, 1)
                )
                self.log.warning(
                    f"Hit the rate limit for VertexAI, retrying in {wait_time} seconds"
                )
                time.sleep(wait_time)
                self.update_depth_ladder(unique_context_id=context_id)
        return response

    def handle_gemini_execution(self, agent: Any, prompt: str, context_id: str = None):
        """
        Helper method to handle Gemini execution

        Args:
            agent: The agent to use (action_agent or output_agent)
            prompt: The fully formatted prompt string
            context_id: A unique identifier for the current browser window

        The `context_id` is to help in differentiating between different browser windows during parallel execution
        for BFS mode.

        `context_id`=None => There is only one browser session.

        Returns:
            response: The raw response from the model. The exact required values
            are expected to be extracted within each agent.
        """
        gemini_config = {
            "response_mime_type": "application/json",
            "response_json_schema": agent["response_format"].model_json_schema(),
            "system_instruction": agent["system_instruction"],
        }

        while True:
            try:
                response = agent["client"].models.generate_content(
                    model=agent["model"],
                    contents=prompt,
                    config=gemini_config,
                )
                self.initialise_depth_ladder(unique_context_id=context_id)
                break
            except Exception:
                wait_time = self.calculate_next_time(
                    self.shared_depth_dictionary.get(context_id, 1)
                )
                self.log.warning(f"Hit the rate limit for Gemini, retrying in {wait_time} seconds")
                time.sleep(wait_time)
                self.update_depth_ladder(unique_context_id=context_id)

        return response

    def calculate_next_time(self, attempt_number):
        """
        Calculates the next backoff wait time in seconds using exponential backoff with jitter.

        Args:
            attempt_number: The number of consecutive failed attempts.
        """

        delay = self.base_timeout * (self.base ** (attempt_number - 1))
        delay = min(delay, self.max_backoff_time)
        jitter = random.uniform(0, delay / 2)
        return delay + jitter

    def initialise_depth_ladder(self, unique_context_id: str):
        """
        Resets the retry counter for a browser session after a successful call.

        Args:
            unique_context_id: The context ID for the current browser session
        """
        self.shared_depth_dictionary[unique_context_id] = 1

    def update_depth_ladder(self, unique_context_id: str):
        """
        Increments the retry counter for a browser session after a failed call.

        Args:
            unique_context_id: The context ID for the browser
        """
        self.shared_depth_dictionary[unique_context_id] += 1
