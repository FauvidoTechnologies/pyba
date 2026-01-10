Exploration Modes
=================

PyBA supports three exploration modes designed for different use cases. This page explains when and how to use each.

.. contents::
   :local:
   :depth: 2

Overview
--------

+----------+---------------------+------------------------------------------+
| Mode     | Use Case            | How It Works                             |
+==========+=====================+==========================================+
| Normal   | Direct tasks        | Execute actions sequentially until done  |
+----------+---------------------+------------------------------------------+
| DFS      | Deep investigation  | One detailed plan at a time, retry with  |
|          |                     | new plans if stuck                       |
+----------+---------------------+------------------------------------------+
| BFS      | Wide discovery      | Multiple plans executed in parallel      |
+----------+---------------------+------------------------------------------+

Normal Mode
-----------

The default mode. Best for straightforward tasks with clear steps.

.. code-block:: python

   from pyba import Engine

   engine = Engine(openai_api_key="sk-...")

   result = engine.sync_run(
       prompt="Go to Wikipedia and find the population of Tokyo"
   )

**When to use Normal mode:**

- Simple, direct tasks
- When the path to completion is clear
- Form filling, single-page scraping
- Quick lookups

**Configuration:**

.. code-block:: python

   engine = Engine(
       openai_api_key="sk-...",
       max_depth=20   # Maximum actions before stopping
   )

DFS Mode (Depth-First Search)
-----------------------------

DFS mode is designed for deep investigation tasks. It generates one detailed plan at a time and executes it fully before generating a new plan based on what was learned.

.. code-block:: python

   from pyba import DFS, Database

   database = Database(engine="sqlite", name="/tmp/pyba.db")

   dfs = DFS(
       openai_api_key="sk-...",
       database=database,
       max_depth=10,    # Actions per plan
       max_breadth=5    # Number of plans to try
   )

   result = dfs.sync_run(
       prompt="Investigate this person's digital footprint across social media"
   )

**How DFS Works:**

1. The **Planner Agent** generates one detailed plan for the task
2. PyBA executes the plan up to ``max_depth`` actions
3. If the goal isn't achieved, it generates a **new plan** based on:

   - What was accomplished
   - What was discovered
   - What didn't work

4. This repeats up to ``max_breadth`` times

**When to use DFS mode:**

- OSINT investigations
- Following chains of information
- Tasks requiring reasoning about intermediate results
- When you need to adapt based on what you find

**Example: Company Research**

.. code-block:: python

   from pyba import DFS, Database

   db = Database(engine="sqlite", name="/tmp/research.db")
   dfs = DFS(openai_api_key="sk-...", database=db)

   result = dfs.sync_run(
       prompt="Research Acme Corp: find their leadership team, recent news, and funding history"
   )

BFS Mode (Breadth-First Search)
-------------------------------

BFS mode explores multiple approaches in parallel. It generates several plans upfront and executes them simultaneously in separate browser windows.

.. code-block:: python

   from pyba import BFS, Database

   database = Database(engine="sqlite", name="/tmp/pyba.db")

   bfs = BFS(
       openai_api_key="sk-...",
       database=database,
       max_depth=10,    # Actions per plan
       max_breadth=5    # Number of parallel plans
   )

   results = bfs.sync_run(
       prompt="Find all social media accounts linked to username 'targetuser123'"
   )

**How BFS Works:**

1. The **Planner Agent** generates ``max_breadth`` different plans
2. Each plan runs in its own browser instance **in parallel**
3. Each plan executes up to ``max_depth`` actions
4. Results from all plans are collected and returned

**When to use BFS mode:**

- Casting a wide net
- When multiple approaches might work
- Searching across different platforms simultaneously
- Discovery tasks

**Example: Social Media Discovery**

.. code-block:: python

   from pyba import BFS, Database

   db = Database(engine="sqlite", name="/tmp/discovery.db")
   bfs = BFS(openai_api_key="sk-...", database=db)

   results = bfs.sync_run(
       prompt="Find information about 'john_doe_123' across Twitter, LinkedIn, GitHub, and Instagram"
   )

   # results is a list with output from each parallel plan
   for i, result in enumerate(results):
       print(f"Plan {i+1}: {result}")

Configuration Reference
-----------------------

All modes share these parameters:

.. code-block:: python

   # Common parameters
   openai_api_key="..."          # Or gemini_api_key, or vertexai_*
   headless=True                  # Browser visibility
   use_logger=False               # Console logging
   enable_tracing=False           # Trace file generation
   trace_save_directory=None      # Where to save traces
   database=None                  # Database instance

   # Mode-specific (DFS and BFS)
   max_depth=10                   # Actions per plan
   max_breadth=5                  # DFS: plans to try, BFS: parallel plans

Choosing the Right Mode
-----------------------

.. list-table::
   :header-rows: 1
   :widths: 30 70

   * - Task Type
     - Recommended Mode
   * - Fill out a form
     - Normal
   * - Scrape a single page
     - Normal
   * - Investigate a person/company
     - DFS
   * - Follow a chain of links
     - DFS
   * - Search multiple platforms
     - BFS
   * - Map out a website
     - BFS
   * - Find accounts across sites
     - BFS
   * - Deep research on one topic
     - DFS

The Planner Agent
-----------------

In DFS and BFS modes, a **Planner Agent** generates high-level plans before execution.

**DFS Planner Output:**

A single detailed plan string that guides the automation.

**BFS Planner Output:**

A list of plan strings, each executed in parallel.

The planner considers:

- The user's task
- Previous plans that were tried (DFS only)
- What approaches might work best

You don't interact with the Planner Agent directly—it's called automatically when using DFS or BFS modes.

Database Requirement
--------------------

.. note::

   DFS and BFS modes work best with a database configured. The database stores:

   - Action history for plan generation
   - Session information across browser instances
   - Logs for debugging and code generation

.. code-block:: python

   from pyba import DFS, BFS, Database

   # Always use a database with DFS/BFS
   db = Database(engine="sqlite", name="/tmp/pyba.db")

   dfs = DFS(openai_api_key="...", database=db)
   bfs = BFS(openai_api_key="...", database=db)

