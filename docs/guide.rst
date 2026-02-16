User Guide
==========

This comprehensive guide covers all of PyBA's features and configuration options.

.. contents::
   :local:
   :depth: 3

Engine Configuration
--------------------

The ``Engine`` class is the main entry point for PyBA. Here are all available options:

.. code-block:: python

   from pyba import Engine, Database

   engine = Engine(
       # LLM Provider (choose one)
       openai_api_key="sk-...",           # OpenAI API key
       gemini_api_key="...",              # Google Gemini API key
       vertexai_project_id="...",         # VertexAI project ID
       vertexai_server_location="...",    # VertexAI region (required with project_id)

       # Model Override
       model_name=None,                   # Override the default model (default: None, uses provider default)

       # Browser Settings
       headless=True,                     # Run without visible browser (default: True)
       handle_dependencies=False,         # Auto-install Playwright deps (default: False)

       # Logging & Tracing
       use_logger=False,                  # Print actions to console (default: False)
       enable_tracing=False,              # Generate trace.zip files (default: False)
       trace_save_directory=None,         # Where to save traces (default: /tmp/pyba/)

       # Execution Limits
       max_depth=20,                      # Max actions per run (default from config)

       # Stealth
       use_random=False,                  # Random mouse/scroll jitters (default: False)

       # Database
       database=None,                     # Database instance for logging

       # Resource Optimization
       low_memory=False,                  # Enable low memory mode (default: False)
   )

Step-by-Step Configuration
--------------------------

The ``Step`` class provides interactive, step-by-step control over a persistent browser:

.. code-block:: python

   from pyba import Step, Database

   step = Step(
       # LLM Provider (choose one)
       openai_api_key="sk-...",           # OpenAI API key
       gemini_api_key="...",              # Google Gemini API key
       vertexai_project_id="...",         # VertexAI project ID
       vertexai_server_location="...",    # VertexAI region

       # Model Override
       model_name=None,                   # Override the default model (default: None, uses provider default)

       # Browser Settings
       headless=False,                    # Always visible by default
       handle_dependencies=False,         # Auto-install Playwright deps

       # Logging & Tracing
       use_logger=False,                  # Print actions to console
       enable_tracing=False,              # Generate trace.zip files
       trace_save_directory=None,         # Where to save traces

       # Step-specific
       max_actions_per_step=5,            # Max actions per instruction (default: 5)
       get_output=False,                  # Ask the model for a summary when a step completes (default: False)

       # Stealth
       use_random=False,                  # Random mouse/scroll jitters

       # Database
       database=None,                     # Database instance for logging

       # Resource Optimization
       low_memory=False,                  # Enable low memory mode (default: False)
   )

**The Step lifecycle:**

.. code-block:: python

   # 1. Launch the browser
   await step.start(automated_login_sites=["instagram"])  # Optional login sites

   # 2. Feed instructions one at a time
   await step.step("Go to my Instagram profile")
   await step.step("Click on the first post")
   output = await step.step("Extract the caption and like count")

   # 3. Shut down
   await step.stop()

Running Tasks
-------------

The ``run()`` Method
^^^^^^^^^^^^^^^^^^^^

The main method for executing browser automation tasks:

.. code-block:: python

   result = engine.sync_run(
       prompt="Your natural language instruction",
       automated_login_sites=["instagram", "gmail"],  # Optional
       extraction_format=MyPydanticModel               # Optional
   )

**Parameters:**

- ``prompt`` (required): Natural language description of what you want to do
- ``automated_login_sites``: List of sites to auto-login (credentials from env vars)
- ``extraction_format``: Pydantic model defining the output structure

Sync vs Async
^^^^^^^^^^^^^

.. code-block:: python

   # Synchronous (blocking)
   result = engine.sync_run(prompt="...")

   # Asynchronous
   import asyncio

   async def main():
       result = await engine.run(prompt="...")

   asyncio.run(main())

Automated Logins
----------------

PyBA includes pre-built login handlers for common platforms. Credentials are stored securely in environment variables.

Setting Up Credentials
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   # Instagram
   export instagram_username=your_username
   export instagram_password=your_password

   # Facebook
   export facebook_username=your_email
   export facebook_password=your_password

   # Gmail
   export gmail_username=your_email
   export gmail_password=your_password

Using Auto-Login
^^^^^^^^^^^^^^^^

.. code-block:: python

   result = engine.sync_run(
       prompt="Go to my Instagram profile and count my followers",
       automated_login_sites=["instagram"]
   )

.. note::

   Credentials are **never** sent to the LLM. The login scripts use hardcoded selectors and execute locally.

2FA Handling
^^^^^^^^^^^^

If a site requires 2FA, PyBA will pause and wait for you to complete it manually. The automation resumes once you're logged in.

Tracing & Debugging
-------------------

PyBA generates Playwright trace files for debugging failed automations.

Enabling Tracing
^^^^^^^^^^^^^^^^

.. code-block:: python

   engine = Engine(
       openai_api_key="...",
       enable_tracing=True,
       trace_save_directory="/path/to/traces"  # Optional, defaults to /tmp/pyba/
   )

   engine.sync_run(prompt="Your task")

Traces are saved as ``<session_id>_trace.zip``.

Viewing Traces
^^^^^^^^^^^^^^

Open traces with Playwright's Trace Viewer:

.. code-block:: bash

   # Online viewer
   # Upload your trace.zip to https://trace.playwright.dev/

   # Local viewer
   npx playwright show-trace /path/to/trace.zip

The trace shows:

- Every action taken
- Network requests
- DOM snapshots
- Console logs
- Screenshots at each step

Stealth Mode
------------

For sites with bot detection, enable stealth features:

.. code-block:: python

   engine = Engine(
       openai_api_key="...",
       use_random=True,   # Enable random movements
       headless=False     # Some sites detect headless browsers
   )

What ``use_random=True`` Does
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

- **Random mouse movements**: Simulates natural cursor movement during waits
- **Scroll jitters**: Adds slight randomness to scrolling
- **Human-like delays**: Varies timing between actions

.. note::

   Stealth mode slightly slows down automation but significantly improves success rate on protected sites.

Error Handling
--------------

PyBA has built-in retry logic with exponential backoff for API errors.

Automatic Retries
^^^^^^^^^^^^^^^^^

When an LLM API call fails (rate limits, timeouts), PyBA automatically:

1. Waits with exponential backoff (1s, 2s, 4s, 8s... up to 60s max)
2. Adds random jitter to prevent thundering herd
3. Retries the request

Action Failures
^^^^^^^^^^^^^^^

When a browser action fails (element not found, timeout), PyBA:

1. Captures the failure reason
2. Re-extracts the current DOM
3. Asks the LLM for an alternative action
4. Logs the failure to the database (if configured)

Logging
-------

Enable verbose logging to see what PyBA is doing:

.. code-block:: python

   engine = Engine(
       openai_api_key="...",
       use_logger=True
   )

Log output includes:

- ``[INFO]`` General information and progress
- ``[ACTION]`` Browser actions being performed
- ``[SUCCESS]`` Completed operations
- ``[WARNING]`` Non-fatal issues
- ``[ERROR]`` Failures and exceptions

Configuration File
------------------

PyBA reads defaults from ``pyba/config.yaml``. You can override these with constructor arguments.

Key configuration sections:

.. code-block:: yaml

   main_engine_configs:
     headless_mode: true
     handle_dependencies: false
     use_logger: false
     enable_tracing: false
     max_iteration_steps: 20
     max_depth: 10          # For DFS/BFS modes
     max_breadth: 5         # For BFS mode

   openai:
     provider: "openai"
     model: "gpt-4o"

   vertexai:
     provider: "vertexai"
     model: "gemini-2.0-flash"

   gemini:
     provider: "gemini"
     model: "gemini-2.5-pro"

Best Practices
--------------

Writing Good Prompts
^^^^^^^^^^^^^^^^^^^^

**Be specific:**

.. code-block:: python

   # Good
   "Go to amazon.com, search for 'wireless headphones', sort by price low to high, and get the name and price of the first 3 results"

   # Too vague
   "Find cheap headphones"

**Break complex tasks into steps:**

.. code-block:: python

   # Good
   "Go to GitHub, navigate to the trending page, filter by Python language, and get the names of the top 5 repositories"

   # Unclear order
   "Get trending Python repos from GitHub"

Low Memory Mode
^^^^^^^^^^^^^^^^

For resource-constrained environments (CI servers, containers, low-spec machines), enable low memory mode to reduce browser resource usage:

.. code-block:: python

   engine = Engine(
       openai_api_key="...",
       low_memory=True
   )

**What low memory mode does:**

- Skips loading ``oxymouse`` (and its dependencies ``numpy``, ``scipy``), saving ~46MB of RAM per process
- Disables GPU rendering (``--disable-gpu``)
- Disables background networking and throttling
- Disables extensions, sync, and default apps
- Sets device scale factor to 1
- Mutes audio

.. note::

   ``low_memory=True`` and ``use_random=True`` cannot be used together.
   Random mouse/scroll movements require ``oxymouse``, which low memory mode excludes to save RAM.

Low memory mode is available on all engine classes: ``Engine``, ``Step``, ``DFS``, and ``BFS``.

.. code-block:: python

   from pyba import Step, DFS, BFS, Database

   # Step mode with low memory
   step = Step(openai_api_key="...", low_memory=True)

   # DFS/BFS with low memory
   db = Database(engine="sqlite", name="/tmp/pyba.db")
   dfs = DFS(openai_api_key="...", database=db, low_memory=True)
   bfs = BFS(openai_api_key="...", database=db, low_memory=True)

Performance Tips
^^^^^^^^^^^^^^^^

1. **Use headless mode** for faster execution (``headless=True``)
2. **Enable low memory mode** on resource-constrained environments (``low_memory=True``)
3. **Enable database logging** only when you need code generation
4. **Set appropriate max_depth** — higher isn't always better
5. **Use extraction_format** when you need structured data

Common Issues
^^^^^^^^^^^^^

**"Element not found"**

- The page may still be loading—try increasing timeouts
- The selector may have changed—enable tracing to debug

**"Rate limit exceeded"**

- PyBA handles this automatically with retries
- Consider using a different LLM provider

**"Login failed"**

- Check your environment variables are set correctly
- The site may have changed their login flow

