from pyba.logger import get_logger
from pyba.utils.exceptions import (
    ServiceNotSelected,
    ServerLocationUndefined,
    UnsupportedModelUsed,
    InvalidModelSelected,
)
from pyba.utils.load_yaml import load_config

config = load_config("general")["main_engine_configs"]


class Provider:
    """
    Class to handle the provider instances.
    """

    def __init__(
        self,
        openai_api_key: str = None,
        gemini_api_key: str = None,
        vertexai_project_id: str = None,
        vertexai_server_location: str = None,
        model_name: str = None,
    ):
        """
        Args:
            openai_api_key: API key for OpenAI models should you want to use that
            vertexai_project_id: Create a VertexAI project to use that instead of OpenAI
            vertexai_server_location: VertexAI server location
            model_name: Model name to use
            gemini_api_key: API key for Gemini models
        """

        self.provider: str | None = None
        self.model: str | None = None
        self.openai_api_key: str | None = openai_api_key
        self.vertexai_project_id: str | None = vertexai_project_id
        self.gemini_api_key: str | None = gemini_api_key
        self.location: str | None = vertexai_server_location
        self.model_name: str | None = model_name

        self.log = get_logger()

        self.handle_keys()  # This figures out the provider we're using and validates that
        self.handle_model(provider=self.provider)

    def handle_keys(self):
        """
        Handles provider selection, defaults to openai when multiple providers conflict
        """
        if (
            self.openai_api_key is None
            and self.vertexai_project_id is None
            and self.gemini_api_key is None
        ):
            raise ServiceNotSelected()

        if self.vertexai_project_id and self.location is None:
            raise ServerLocationUndefined(self.location)

        if (
            (self.openai_api_key and self.vertexai_project_id)
            or (self.vertexai_project_id and self.gemini_api_key)
            or (self.openai_api_key and self.gemini_api_key)
        ):
            if self.openai_api_key:
                self.log.warning("Multiple LLM keys defined, defaulting to OpenAI")
                self.provider = config["openai"]["provider"]
                self.vertexai_project_id = None
                self.location = None
                self.gemini_api_key = None
            elif self.vertexai_project_id:
                self.log.warning("Multiple LLM keys defined, defaulting to VertexAI")
                self.provider = config["vertexai"]["provider"]
                self.gemini_api_key = None
            else:
                self.log.warning("Multiple LLM keys defined, defaulting to Gemini")
                self.provider = config["gemini"]["provider"]
                self.vertexai_project_id = None
                self.location = None

        elif self.vertexai_project_id:
            self.provider = config["vertexai"]["provider"]
        elif self.openai_api_key:
            self.provider = config["openai"]["provider"]
        else:
            self.provider = config["gemini"]["provider"]

    def handle_model(self, provider: str):
        """
        Helper function that manages model selection based on the keys chosen.

        Note:
            The default models in config will be used if model name is not
            provided by the user. The list of valid model names will be present
            in the config file as well.

        Args:
            provider: The name of the provider in question
        """
        if not self.model_name:  # Default model based on provider
            self.model = config[self.provider]["model"]
            return

        self.valid_models: dict = {
            "vertexai_models": config["vertexai"]["available_models"],
            "openai_models": config["openai"]["available_models"],
            "gemini_models": config["gemini"]["available_models"],
        }

        if self.model_name not in [j for model in self.valid_models.values() for j in model]:
            raise UnsupportedModelUsed(
                model_name=self.model_name,
                valid_model_names=[j for model in self.valid_models.values() for j in model],
            )

        if self.model_name not in self.valid_models.get(f"{self.provider}_models"):
            raise InvalidModelSelected(
                model_name=self.model_name,
                provider=self.provider,
                provider_valid_models=self.valid_models.get(self.provider),
            )
        else:
            self.model = self.model_name
