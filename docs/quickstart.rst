Quickstart
==========

Get up and running with PyBA in under 5 minutes.

.. contents::
   :local:
   :depth: 2

Basic Usage
-----------

The simplest way to use PyBA:

.. code-block:: python

   from pyba import Engine

   # Initialize with your preferred provider
   engine = Engine(openai_api_key="sk-...")

   # Run a task
   result = engine.sync_run(prompt="Go to news.ycombinator.com and get the top 3 headlines")
   print(result)

That's it! The AI will navigate to Hacker News and extract the headlines.

Async vs Sync
-------------

PyBA supports both synchronous and asynchronous execution:

**Synchronous** (simpler, blocking):

.. code-block:: python

   result = engine.sync_run(prompt="Your task here")

**Asynchronous** (for async codebases):

.. code-block:: python

   import asyncio

   async def main():
       result = await engine.run(prompt="Your task here")
       print(result)

   asyncio.run(main())

Watch It Work
-------------

By default, PyBA runs headless (no visible browser). To see what it's doing:

.. code-block:: python

   engine = Engine(
       openai_api_key="sk-...",
       headless=False,      # Show the browser window
       use_logger=True      # Print actions to console
   )

   engine.sync_run(prompt="Search for 'python tutorials' on Google")

Export to Script
----------------

The killer feature—export any successful run as a standalone Playwright script:

.. code-block:: python

   from pyba import Engine, Database

   # Database is required for code generation
   db = Database(engine="sqlite", name="/tmp/pyba.db")

   engine = Engine(
       openai_api_key="sk-...",
       database=db
   )

   # Run the automation
   engine.sync_run(prompt="Go to GitHub trending and get the top repository")

   # Export as reusable script
   engine.generate_code(output_path="github_trending.py")

Now you can run ``python github_trending.py`` forever without AI costs!

Different Providers
-------------------

PyBA works with multiple LLM providers:

.. code-block:: python

   from pyba import Engine

   # OpenAI (defaults to gpt-4o)
   engine = Engine(openai_api_key="sk-...")

   # OpenAI with a specific model
   engine = Engine(openai_api_key="sk-...", model_name="gpt-4o-mini")

   # Google Gemini (defaults to gemini-2.5-pro)
   engine = Engine(gemini_api_key="your-gemini-key")

   # Google VertexAI (defaults to gemini-2.0-flash)
   engine = Engine(
       vertexai_project_id="your-project",
       vertexai_server_location="us-central1"
   )

Authenticated Sites
-------------------

Need to login to a site? PyBA has built-in login handlers:

.. code-block:: python

   # First, set credentials as environment variables
   # export instagram_username=your_username
   # export instagram_password=your_password

   engine = Engine(openai_api_key="sk-...")

   result = engine.sync_run(
       prompt="Go to my Instagram feed and get the first 5 post captions",
       automated_login_sites=["instagram"]
   )

Supported sites: ``instagram``, ``facebook``, ``gmail``

.. note::

   Credentials are stored in environment variables and **never** sent to the LLM.

Structured Data Extraction
--------------------------

Extract data in a specific format using Pydantic models:

.. code-block:: python

   from pydantic import BaseModel
   from pyba import Engine

   class Product(BaseModel):
       name: str
       price: str
       rating: str

   engine = Engine(openai_api_key="sk-...")

   result = engine.sync_run(
       prompt="Go to Amazon and find the top 3 laptops under $1000",
       extraction_format=Product
   )

Enable Tracing
--------------

Generate trace files for debugging with Playwright Trace Viewer:

.. code-block:: python

   engine = Engine(
       openai_api_key="sk-...",
       enable_tracing=True,
       trace_save_directory="/tmp/traces"
   )

   engine.sync_run(prompt="Your task here")

   # Open the trace with: npx playwright show-trace /tmp/traces/<session_id>_trace.zip

Step-by-Step Mode
-----------------

Want to control the browser interactively, one instruction at a time?

.. code-block:: python

   from pyba import Step

   step = Step(openai_api_key="sk-...")

   # Launch a persistent browser
   await step.start()

   # Feed instructions one at a time
   await step.step("Go to news.ycombinator.com")
   await step.step("Click the top story")
   output = await step.step("Extract the title and all comments")
   print(output)

   # Done
   await step.stop()

The browser stays open between ``step()`` calls, so you can inspect results and decide what to do next.

**Synchronous version:**

.. code-block:: python

   step = Step(openai_api_key="sk-...")
   step.sync_start()
   step.sync_step("Go to news.ycombinator.com")
   output = step.sync_step("Get the top 3 headlines")
   step.sync_stop()

Next Steps
----------

- :doc:`guide` — Full feature walkthrough
- :doc:`modes` — Learn about Normal, Step, DFS and BFS exploration modes
- :doc:`cli` — Use PyBA from the command line
- :doc:`architecture` — Understand how PyBA works internally

