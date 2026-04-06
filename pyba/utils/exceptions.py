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


class CamoufoxNotInstalled(Exception):
    """
    Exception raised when camoufox is enabled but the package is not installed.
    """

    def __init__(self):
        super().__init__(
            "Camoufox is enabled but not installed. "
            "Install it with: poetry install -E camoufox (or pip install -U camoufox)"
        )


class CannotResolveError(Exception):
    """
    Exception to be rasied when the user provides a PasswordManager class which requires
    positional arguments to be specified.
    """

    def __init__(self):
        super().__init__(
            "Unable to resolve the secrets from your password manager. Please make sure that you pass in an 'instance' of your password manager"
        )


# ---------------------------------------------------------------------------
# Structured runtime errors for better user-facing error reporting
# ---------------------------------------------------------------------------


class PybaError(Exception):
    """
    Base class for all structured runtime errors raised by Pyba.

    Every subclass carries a human-readable ``message`` and the original
    ``cause`` exception (if any) so callers can inspect both without
    parsing tracebacks.
    """

    category: str = "unknown"

    def __init__(self, message: str, cause: Exception = None):
        self.message = message
        self.cause = cause
        super().__init__(message)

    def __str__(self):
        if self.cause:
            return f"[{self.category}] {self.message} (caused by {type(self.cause).__name__}: {self.cause})"
        return f"[{self.category}] {self.message}"


class ActionError(PybaError):
    """An action dispatched to Playwright failed."""

    category = "action"


class ElementNotFoundError(ActionError):
    """A selector did not match any element on the page."""

    category = "element_not_found"


class ActionTimeoutError(ActionError):
    """A Playwright action exceeded its timeout."""

    category = "timeout"


class NavigationError(ActionError):
    """A page navigation (goto, back, forward, reload) failed."""

    category = "navigation"


class LLMError(PybaError):
    """The LLM provider returned an error or an unparseable response."""

    category = "llm"


class LLMRateLimitError(LLMError):
    """The LLM provider rate-limited the request."""

    category = "llm_rate_limit"


class LLMResponseParseError(LLMError):
    """The LLM returned a response that could not be parsed into an action."""

    category = "llm_parse"
