Installation
============

This guide covers how to install PyBA and its dependencies.

.. contents::
   :local:
   :depth: 2

From PyPI
---------

The recommended way to install PyBA:

.. code-block:: bash

   pip install py-browser-automation

From Source
-----------

For development or to get the latest changes:

.. code-block:: bash

   git clone https://github.com/fauvidoTechnologies/PyBrowserAutomation.git
   cd PyBrowserAutomation
   pip install -e .

Using Poetry
^^^^^^^^^^^^

If you prefer Poetry for dependency management:

.. code-block:: bash

   git clone https://github.com/fauvidoTechnologies/PyBrowserAutomation.git
   cd PyBrowserAutomation
   poetry install

Browser Dependencies
--------------------

PyBA uses Playwright under the hood. After installing PyBA, you need to install browser binaries:

**Option 1: Automatic** (recommended)

Let PyBA handle it by setting ``handle_dependencies=True``:

.. code-block:: python

   from pyba import Engine

   engine = Engine(openai_api_key="...", handle_dependencies=True)

**Option 2: Manual**

Install browsers and system dependencies yourself:

.. code-block:: bash

   # Install browser binaries
   playwright install

   # Install system dependencies (Linux only)
   playwright install-deps

**Option 3: Using the DependencyManager**

.. code-block:: python

   from pyba.core import DependencyManager

   DependencyManager.playwright.handle_dependencies()

LLM Provider Setup
------------------

PyBA supports three LLM providers. You need at least one configured.

OpenAI
^^^^^^

1. Get an API key from `OpenAI Platform <https://platform.openai.com/>`_
2. Pass it directly or set as environment variable:

.. code-block:: python

   # Direct
   engine = Engine(openai_api_key="sk-...")

   # Or via environment
   import os
   os.environ["OPENAI_API_KEY"] = "sk-..."
   engine = Engine(openai_api_key=os.environ["OPENAI_API_KEY"])

Google Gemini
^^^^^^^^^^^^^

1. Get an API key from `Google AI Studio <https://aistudio.google.com/>`_
2. Use it in PyBA:

.. code-block:: python

   engine = Engine(gemini_api_key="your-gemini-key")

Google VertexAI
^^^^^^^^^^^^^^^

1. Set up a GCP project with VertexAI enabled
2. Configure authentication (``gcloud auth application-default login``)
3. Use it in PyBA:

.. code-block:: python

   engine = Engine(
       vertexai_project_id="your-project-id",
       vertexai_server_location="us-central1"
   )

Verifying Installation
----------------------

Run a quick test to verify everything works:

.. code-block:: python

   from pyba import Engine

   engine = Engine(openai_api_key="your-key", handle_dependencies=True)
   result = engine.sync_run(prompt="Go to example.com and tell me the page title")
   print(result)

If you see output about the page title, you're all set!

Platform Support
----------------

PyBA is tested on:

- **Linux**: Ubuntu 20.04+, Debian 10+
- **macOS**: 11 (Big Sur) and later
- **Windows**: Windows 10/11

.. note::

   On Linux servers without a display, use ``headless=True`` (this is the default).

