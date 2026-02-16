class PromptNotPresent(Exception):
    """
    This exception is raised when the user forgets to enter a prompt to the engine
    """

    def __init__(self):
        super().__init__("Please provide a prompt for us to work on")


class ServiceNotSelected(Exception):
    """
    This exception is raised when the user doesn't set an API key in the engine
    """

    def __init__(self):
        super().__init__("Please set either a VertexAI project ID or an OpenAI key")


class ServerLocationUndefined(Exception):
    """
    This exception is raised when the user doesn't define the server location
    for a VertexAI project.
    """

    def __init__(self, server_location):
        super().__init__(
            f"The server location {server_location} is undefined. Please visit https://cloud.google.com/vertex-ai/docs/general/locations and choose a location that your credits are tied to."
        )


class CredentialsNotSpecified(Exception):
    """
    Exception raised in the login scripts when the relevant credentials haven't been specified
    """

    def __init__(self, site_name: str):
        super().__init__(f"Please specify all the credentials for the {site_name} engine.")


class UnknownSiteChosen(Exception):
    """
    Exception to be raised when the user chooses a site for automated login that isn't implemented yet.
    """

    def __init__(self, sites: list):
        super().__init__(
            f"Unknown site chosen for automated login. The following sites are available: {sites}"
        )


class DatabaseNotInitialised(Exception):
    """
    Exception to be raised when the user asks for automation code generation but has not initialised the database!
    """

    def __init__(self):
        super().__init__(
            "Tried to call for code-generation without logging in a database! Please initialise the database."
        )


class IncorrectMode(Exception):
    """
    Exception to be raised when the mode specified by the user is incorrect
    """

    def __init__(self, mode: str):
        super().__init__(
            f"Mode {mode} is not supported. Please choose between DFS or BFS and enter as a string"
        )


class UnsupportedModelUsed(Exception):
    """
    Exception to be raised when the model specified by the user is not supported
    """

    def __init__(self, model_name: str, valid_model_names: list):
        super().__init__(
            f"The model {model_name} is not supported. Please choose one from {valid_model_names}"
        )


class InvalidModelSelected(Exception):
    """
    Exception to be raised when the model chosen by the user doesn't fall under the
    provider for whom the keys are specified
    """

    def __init__(self, model_name: str, provider: str, provider_valid_models: list):
        super().__init__(
            f"The model {model_name} is not supported by the provider {provider}. For the provider specified, please choose from the following: {provider_valid_models}"
        )
