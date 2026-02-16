Command Line Interface
======================

PyBA includes a CLI for running automations directly from your terminal.

.. contents::
   :local:
   :depth: 2

Installation
------------

The CLI is installed automatically with PyBA:

.. code-block:: bash

   pip install py-browser-automation

   # Verify installation
   pyba --version

Quick Start
-----------

Run a simple task:

.. code-block:: bash

   pyba normal -t "go to example.com and find the contact page" --openai-api-key "sk-..."

Modes
-----

The CLI has three main modes:

normal
^^^^^^

Quick ad-hoc runs without database logging:

.. code-block:: bash

   pyba normal -t "search for cheap headphones on amazon.in" --openai-api-key "sk-..."

database
^^^^^^^^

Stores logs in a database for auditing and code generation:

.. code-block:: bash

   pyba database \
     -e sqlite \
     -n /tmp/pyba.db \
     -t "search amazon for birthday gifts" \
     --openai-api-key "sk-..."

Global Flags
------------

These flags work with both modes:

LLM Provider
^^^^^^^^^^^^

.. code-block:: bash

   # OpenAI
   --openai-api-key "sk-..."

   # Google Gemini
   --gemini-api-key "your-key"

   # VertexAI
   --vertexai-project-id "project-id" --vertexai-server-location "us-central1"

   # Override the default model for any provider
   --model-name "gpt-4.1"

Task
^^^^

.. code-block:: bash

   -t, --task "Your natural language task"

Browser Options
^^^^^^^^^^^^^^^

.. code-block:: bash

   --headless          # Run without visible browser
   --handle-deps       # Auto-install Playwright dependencies

Logging & Tracing
^^^^^^^^^^^^^^^^^

.. code-block:: bash

   -v                  # Verbose logging
   --enable-tracing    # Generate trace.zip files
   --trace-save-dir    # Directory for trace files

Low Memory
^^^^^^^^^^

.. code-block:: bash

   --low-memory-usage        # Enable low memory mode

Saves ~327MB total: ~119MB from Python-side lazy imports (oxymouse, LLM providers) and ~208MB from Chromium process optimizations (single-process mode, V8 heap cap, disabled site isolation). Cannot be used with ``-r``. Useful for CI servers, containers, or low-spec machines.

Stealth
^^^^^^^

.. code-block:: bash

   -r                  # Enable random mouse/scroll movements

Automated Login
^^^^^^^^^^^^^^^

.. code-block:: bash

   -L instagram -L facebook    # Login to specified sites

Exploration Modes
^^^^^^^^^^^^^^^^^

.. code-block:: bash

   --op-mode Normal    # Default autonomous mode
   --op-mode STEP      # Interactive step-by-step mode
   --op-mode DFS       # Depth-first search
   --op-mode BFS       # Breadth-first search

   --max-depth 10      # Actions per plan (DFS/BFS)
   --max-breadth 5     # Number of plans (BFS) or retries (DFS)

Database Mode Flags
-------------------

These flags are specific to ``pyba database``:

Engine Selection
^^^^^^^^^^^^^^^^

.. code-block:: bash

   -e, --engine sqlite|mysql|postgres

Database Connection
^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   -n, --name /path/to/db.db    # SQLite: file path, Others: database name
   -u, --username user          # MySQL/PostgreSQL
   -p, --password pass          # MySQL/PostgreSQL
   -H, --host-name localhost    # MySQL/PostgreSQL
   -P, --port 5432              # MySQL/PostgreSQL
   --ssl-mode disabled|required # PostgreSQL only

Code Generation
^^^^^^^^^^^^^^^

.. code-block:: bash

   --generate-code                    # Enable script generation
   --code-output-path /tmp/script.py  # Where to save the script

Examples
--------

Simple Search (Normal Mode)
^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   pyba normal \
     -t "find the CSE contact page for IIT Madras" \
     --openai-api-key "sk-..." \
     -v

Database Mode with SQLite
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   pyba database \
     -e sqlite \
     -n /tmp/pyba.db \
     -t "search amazon.in for birthday gifts under 5000 INR" \
     --openai-api-key "sk-..." \
     -v \
     --enable-tracing \
     --trace-save-dir /tmp/traces

Low Memory Mode
^^^^^^^^^^^^^^^^

.. code-block:: bash

   pyba normal \
     -t "scrape data from example.com" \
     --openai-api-key "sk-..." \
     --low-memory-usage

Full Featured Run
^^^^^^^^^^^^^^^^^

.. code-block:: bash

   pyba database \
     -e sqlite \
     -n /tmp/pyba.db \
     -t "go to Amazon India, find gifts under 5k, then message the list on Instagram" \
     --vertexai-project-id "my-project" \
     --vertexai-server-location "us-central1" \
     --handle-deps \
     --enable-tracing \
     --trace-save-dir /tmp/traces \
     -v \
     -r \
     -L instagram \
     -L amazon \
     --generate-code \
     --code-output-path /tmp/automation.py

PostgreSQL Database
^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   pyba database \
     -e postgres \
     -n pyba_db \
     -u dbuser \
     -p "dbpassword" \
     -H 192.168.1.10 \
     -P 5432 \
     -t "your task here" \
     --openai-api-key "sk-..."

Using Gemini
^^^^^^^^^^^^

.. code-block:: bash

   export GEMINI_API_KEY="your-key"

   pyba database \
     -e sqlite \
     -n /tmp/pyba.db \
     -t "search for Python tutorials" \
     --gemini-api-key "$GEMINI_API_KEY"

Step-by-Step Mode
^^^^^^^^^^^^^^^^^

In STEP mode, the CLI launches a persistent browser and reads instructions from the terminal one at a time:

.. code-block:: bash

   pyba normal \
     --op-mode STEP \
     --openai-api-key "sk-..."

You will be prompted for instructions interactively:

.. code-block:: text

   >> Go to youtube.com
   >> Search for rickroll
   >> Click the first video
   >> quit

Type ``quit`` to stop the session.

BFS Exploration Mode
^^^^^^^^^^^^^^^^^^^^

.. code-block:: bash

   pyba database \
     -e sqlite \
     -n /tmp/pyba.db \
     -t "find social media accounts for username 'johndoe123'" \
     --openai-api-key "sk-..." \
     --op-mode BFS \
     --max-breadth 5 \
     --max-depth 10

Environment Variables
---------------------

For security, use environment variables instead of command-line arguments:

.. code-block:: bash

   # API Keys
   export OPENAI_API_KEY="sk-..."
   export GEMINI_API_KEY="..."

   # Login credentials
   export instagram_username="your_user"
   export instagram_password="your_pass"
   export facebook_username="your_email"
   export facebook_password="your_pass"

Then reference them:

.. code-block:: bash

   pyba normal -t "your task" --openai-api-key "$OPENAI_API_KEY"

Getting Help
------------

.. code-block:: bash

   # General help
   pyba --help

   # Mode-specific help
   pyba normal --help
   pyba database --help

   # Version
   pyba --version
   pyba -V

Troubleshooting
---------------

Database Engine Error
^^^^^^^^^^^^^^^^^^^^^

If you see:

.. code-block:: text

   Wrong database engine chosen. Please choose from sqlite, mysql or postgres

Make sure ``-e`` is one of: ``sqlite``, ``mysql``, ``postgres``

Trace Files Not Appearing
^^^^^^^^^^^^^^^^^^^^^^^^^

- Check that ``--enable-tracing`` is set
- Verify ``--trace-save-dir`` exists and is writable
- Use ``-v`` to see where traces are saved

Credentials Not Working
^^^^^^^^^^^^^^^^^^^^^^^

- Ensure environment variables are exported in the **same shell** running ``pyba``
- Variable names must match exactly: ``instagram_username``, ``instagram_password``, etc.

Headless Failing on Servers
^^^^^^^^^^^^^^^^^^^^^^^^^^^

- Use ``--handle-deps`` to install required system libraries
- On Linux, you may need: ``sudo apt install libnss3 libatk-bridge2.0-0 libcups2``

High Memory Usage
^^^^^^^^^^^^^^^^^

- Use ``--low-memory-usage`` to save ~327MB total (~119MB Python + ~208MB Chromium)
- Merges Chromium into a single process, caps V8 heap, skips unused Python dependencies
- Cannot be combined with ``-r`` (random mouse movements)
- Recommended for CI/CD pipelines, Docker containers, and low-spec servers
