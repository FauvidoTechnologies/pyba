from typing import Tuple, Dict, Optional

from pydantic import BaseModel

from pyba.utils.exceptions import IncorrectMode
from pyba.utils.load_yaml import load_config
from pyba.utils.prompts import (
    system_instruction,
    step_system_instruction,
    output_system_instruction,
    BFS_planner_system_instruction,
    DFS_planner_system_instruction,
    extraction_system_instruction,
)
from pyba.utils.structure import (
    PlaywrightResponse,
    OutputResponseFormat,
    PlannerAgentOutputBFS,
    PlannerAgentOutputDFS,
    GeneralExtractionResponse,
)

config = load_config("general")


class LLMFactory:
    """
    Class for handling different types of LLM. The supported LLMs are:

    1. OpenAI - GPT-4o, GPT-3.5-turbo
    2. VertexAI - Gemini-2.5-pro
    3. Native gemini-2.5-pro API
    """

    def __init__(self, engine):
        """
        Initialise the engine parameters as given by the user

        Args;
                engine: The LLM parameters provided by the user
        """
        self.engine = engine
        self.vertexai_client = None
        self.openai_client = None
        self.gemini_client = None

        if self.engine.provider == "openai":
            self.openai_client = self._initialize_openai_client()
        elif self.engine.provider == "vertexai":
            self.vertexai_client = self._initialize_vertexai_client()
        else:
            self.gemini_client = self._initialize_gemini_client()

        self.mode = self.engine.mode  # Mode of operation for Exploratory, DFS|BFS

    def _initialize_vertexai_client(self):
        """
        Initialises the VertexAI client using engine parameters
        """

        from google import genai

        vertexai_client = genai.Client(
            vertexai=True, project=self.engine.vertexai_project_id, location=self.engine.location
        )

        return vertexai_client

    def _initialize_vertexai_agent(self, system_instruction: str, response_schema):
        """
        Initiaises a VertexAI agent

        Args:
                `system_instruction`: The system instruction for the agent
                `response_schema`: The response schema for the Agent
        """
        assert system_instruction is not None and response_schema is not None

        from google.genai.types import GenerateContentConfig

        agent = self.vertexai_client.chats.create(
            model=self.engine.model,
            config=GenerateContentConfig(
                temperature=0,
                system_instruction=system_instruction,
                response_schema=response_schema,
                response_mime_type="application/json",
            ),
        )

        return agent

    def _initialize_openai_client(self):
        """
        Initialize the OpenAI client using engine parameters
        """
        from openai import OpenAI

        openai_client = OpenAI(api_key=self.engine.openai_api_key)
        return openai_client

    def _initialize_openai_agent(self, system_instruction: str, response_schema) -> Dict:
        """
        Initialize the OpenAI agent

        Args:
                `system_instruction`: The system instruction for the agent
                `response_schema`: The response type for the agent

        Returns:
                Dictionary of the agent parameters
        """

        agent = {
            "client": self.openai_client,
            "system_instruction": system_instruction,
            "model": config["main_engine_configs"]["openai"]["model"],
            "response_format": response_schema,
        }

        return agent

    def _initialize_gemini_client(self):
        """
        Initialises the native gemini-2.5-pro client (without VertexAI)
        """
        from google import genai

        gemini_client = genai.Client(vertexai=False, api_key=self.engine.gemini_api_key)
        return gemini_client

    def _initialize_gemini_agent(self, system_instruction: str, response_schema) -> Dict:
        """
        Initilse the Gemini Agent

        Args:
            `system_instruction`: The system instruction for the agent
            `response_schema`: The response type for the agent

        Returns:
            Dictionary of the agent parameters
        """
        agent = {
            "client": self.gemini_client,
            "system_instruction": system_instruction,
            "model": self.engine.model,
            "response_format": response_schema,
        }

        return agent

    def create_agentic_pair(self, init_method) -> Tuple:
        """
        Create the action and output agents for different LLMs

        Args:
            `init_method`: Function to initialise the respective LLM agent

        Returns:
            A tuple containing the action and output agent
        """

        prompts = step_system_instruction if self.mode == "STEP" else system_instruction
        action_system = prompts[self.engine.provider]

        action_agent = init_method(
            system_instruction=action_system, response_schema=PlaywrightResponse
        )
        output_agent = init_method(
            system_instruction=output_system_instruction, response_schema=OutputResponseFormat
        )

        return (action_agent, output_agent)

    def create_planner_agent(self, init_method):
        """
        Helper function to return the appropriate planner agent

        Args:
            `init_method`: Function to initialise the respective LLM agent

        Returns:
            A planner agent instance
        """
        if self.mode == "BFS":
            system_instruction = BFS_planner_system_instruction
            response_schema = PlannerAgentOutputBFS
        else:
            system_instruction = DFS_planner_system_instruction
            response_schema = PlannerAgentOutputDFS

        planner_agent = init_method(
            system_instruction=system_instruction, response_schema=response_schema
        )

        return planner_agent

    def create_extraction_agent(self, init_method, response_format=None):
        """
        Helper function to return the appropriate extraction agent

        Args:
            `init_method`: Function to initialise the respective LLM agent
            `response_format`: The response output type for the extraction agent
        """

        if response_format:
            extraction_agent = init_method(
                system_instruction=extraction_system_instruction, response_schema=response_format
            )
        else:
            extraction_agent = init_method(
                system_instruction=extraction_system_instruction,
                response_schema=GeneralExtractionResponse,
            )

        return extraction_agent

    def get_agent(self) -> Tuple:
        """
        Endpoint to return the agents depending on the LLM called for

        Returns:
                A tuple containing the main agent and the output agent for a particular provider
        """
        if self.engine.provider == "openai":
            init_method = self._initialize_openai_agent
        elif self.engine.provider == "vertexai":
            init_method = self._initialize_vertexai_agent
        else:
            init_method = self._initialize_gemini_agent

        agents = self.create_agentic_pair(init_method)

        return agents

    def get_planner_agent(self):
        """
        Endpoint to return the planner agent depending on the LLM called for. If
        this endpoint is called, the mode must be specified correctly.

        Args:
            `mode`: DFS|BFS|STEP. ALl three of these modes have their own system prompts.

        The mode must be specified. If mode is None, then planner-agent shouldn't be called.

        Returns:
            A single agent for a particular provider
        """

        if self.mode not in ("BFS", "DFS", "Normal", "STEP"):
            raise IncorrectMode(mode=self.mode)

        if self.engine.provider == "openai":
            init_method = self._initialize_openai_agent
        elif self.engine.provider == "vertexai":
            init_method = self._initialize_vertexai_agent
        else:
            init_method = self._initialize_gemini_agent

        planner_agent = self.create_planner_agent(init_method)

        return planner_agent

    def get_extraction_agent(self, extraction_format: Optional[BaseModel]):
        """
        Endpoint to return the extraction agent depending on the LLM called for.

        Args:
            `extraction_format`: This is the extraction format which is expected, it can be `None`
        """

        if self.engine.provider == "openai":
            init_method = self._initialize_openai_agent
        elif self.engine.provider == "vertexai":
            init_method = self._initialize_vertexai_agent
        else:
            init_method = self._initialize_gemini_agent

        agent = self.create_extraction_agent(init_method, response_format=extraction_format)

        return agent
