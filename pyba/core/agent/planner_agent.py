import json
from typing import Union, Any

from pyba.core.agent.base_agent import BaseAgent
from pyba.utils.load_yaml import load_config
from pyba.utils.prompts import planner_general_prompt_DFS, planner_general_prompt_BFS
from pyba.utils.structure import PlannerAgentOutputBFS, PlannerAgentOutputDFS

config = load_config("general")["main_engine_configs"]


class PlannerAgent(BaseAgent):
    """
    Planner agent for DFS and BFS modes under exploratory cases. This is inheriting off
    from the Retry class as well and supports all agents under LLM_factory.

    Args:
            `engine`: Engine to hold all arguments provided by the user

    Initialises the `max_breadth` for the maximum number of plans to generate for BFS mode

    NOTE:
        `context_id` is not relevant here because this is a higer level class
    """

    def __init__(self, engine) -> None:
        """
        Initialises the right agent from the LLMFactory
        """
        super().__init__(engine=engine)  # Initialising the base params from BaseAgent
        self.agent = self.llm_factory.get_planner_agent()
        self.max_breadth = config["max_breadth"]

    def _initialise_prompt(self, task: str, old_plan: str = None):
        """
                Initialise the prompt for the planner agent

        Args:
                `task`: Task given by the user
                `old_plan`: The previous plan in case of DFS mode
        """
        if self.mode == "BFS":
            return planner_general_prompt_BFS.format(task=task, max_plans=self.max_breadth)
        else:
            return planner_general_prompt_DFS.format(task=task, old_plan=old_plan)

    def _call_model(self, agent: Any, prompt: str) -> Any:
        """
        Generic method to call the correct LLM provider and parse the response.

        Args:
            agent: The agent to use (action_agent or output_agent)
            prompt: The fully formatted prompt string

        Returns:
            The parsed response (SimpleNamespace for action, str for output)

        Uses the attempt_number to give ou
        """
        if self.engine.provider == "openai":
            response = self.handle_openai_execution(agent=agent, prompt=prompt)
            parsed_json = json.loads(response.choices[0].message.content)

            if "plans" in list(parsed_json.keys()):
                return parsed_json["plans"]
            if "plan" in list(parsed_json.keys()):
                return parsed_json["plan"]
            self.log.error("Parsed object has neither 'plans' nor 'plan' attribute.")
            return None

        elif self.engine.provider == "vertexai":  # VertexAI logic
            response = self.handle_vertexai_execution(agent=agent, prompt=prompt)
            try:
                parsed_object = getattr(
                    response, "output_parsed", getattr(response, "parsed", None)
                )

                if not parsed_object:
                    self.log.error("No parsed object found in VertexAI response.")
                    return None

                if hasattr(parsed_object, "plans"):
                    return parsed_object.plans

                if hasattr(parsed_object, "plan"):
                    return parsed_object.plan

                self.log.error("Parsed object has neither 'plans' nor 'plan' attribute.")
                return None

            except Exception as e:
                self.log.error(f"Unable to parse the output from VertexAI response: {e}")
                return None

        else:  # Using gemini
            response = self.handle_gemini_execution(agent=agent, prompt=prompt)
            action = agent["response_format"].model_validate_json(response.text)

            if hasattr(action, "plan"):
                return action.plan

            elif hasattr(action, "plans"):
                return action.plans

            else:
                self.log.error("Parsed object has neither 'plans' nor 'plan' attribute.")
                return None

    def generate(
        self, task: str, old_plan: str = None
    ) -> Union[PlannerAgentOutputBFS, PlannerAgentOutputDFS]:
        """
        Endpoint to generate the plan(s) depending on the set mode (the agent encodes the mode)

        Args:
            `task`: The task provided by the user
            `old_plan`: The previous plan if using DFS mode

        Function:
            - Takes in the user prompt which serves as the task for the model to perform
            - Depending on DFS or BFS mode generates plan(s)
        """
        prompt = self._initialise_prompt(task=task, old_plan=old_plan)
        return self._call_model(agent=self.agent, prompt=prompt)
