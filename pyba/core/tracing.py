from pathlib import Path

from pyba.utils.load_yaml import load_config
from pyba.utils.low_memory import CONTEXT_KWARGS as LOW_MEMORY_CONTEXT_KWARGS

config = load_config("general")["main_engine_configs"]

DEFAULT_VIEWPORT = {"width": 1920, "height": 1080}


class Tracing:
    def __init__(
        self,
        browser_instance,
        session_id: str,
        enable_tracing: bool = False,
        trace_save_directory: str = None,
        screenshots: bool = False,
        snapshots: bool = False,
        sources: bool = False,
        low_memory: bool = False,
    ):
        """
        Args:
            browser_instance: The browser instance being used under the main async with statement
            session_id: A unique identifier for this session
            enable_tracing: A boolean to indicate the use of tracing
            trace_save_directory: Directory to save the traces
            screenshots: Enable screenshot taking during tracing
            snapshots: Enable capturing snapshots during tracing
            sources: Enable sources during tracing
            low_memory: Enable low memory mode by reducing the viewport and disabling features
        """

        self.browser = browser_instance

        self.session_id = session_id
        self.enable_tracing = enable_tracing
        self.trace_save_directory = trace_save_directory
        self.low_memory = low_memory

        self.screenshots: bool = config["tracing"]["screenshots"] | screenshots
        self.snapshots: bool = config["tracing"]["snapshots"] | snapshots
        self.sources: bool = config["tracing"]["sources"] | sources

        if self.trace_save_directory is None:
            trace_save_directory = str(Path.cwd())
        else:
            trace_save_directory = self.trace_save_directory

        self.trace_dir = Path(trace_save_directory)
        self.trace_dir.mkdir(parents=True, exist_ok=True)

        self.har_file_path = self.trace_dir / f"{self.session_id}_network.har"

    async def initialize_context(self):
        context_kwargs = {"viewport": DEFAULT_VIEWPORT}
        if self.low_memory:
            context_kwargs.update(LOW_MEMORY_CONTEXT_KWARGS)

        if self.enable_tracing:
            context_kwargs["record_har_path"] = self.har_file_path
            context_kwargs["record_har_content"] = config["tracing"]["record_har_content"]

            context = await self.browser.new_context(**context_kwargs)

            await context.tracing.start(
                screenshots=self.screenshots,
                snapshots=self.snapshots,
                sources=self.sources,
            )

        else:
            context = await self.browser.new_context(**context_kwargs)

        return context
