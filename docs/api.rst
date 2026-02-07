API Reference
=============

This page documents the public API of PyBA. For internal architecture details, see :doc:`architecture`.

.. contents::
   :local:
   :depth: 2

Entry Points
------------

Engine
^^^^^^

The main entry point for autonomous browser automation.

.. autoclass:: pyba.core.main.Engine
   :members:
   :undoc-members:
   :show-inheritance:

Step (Step-by-Step)
^^^^^^^^^^^^^^^^^^^

Entry point for interactive step-by-step mode. The user controls the browser one instruction at a time via ``start()``, ``step()``, and ``stop()``.

.. autoclass:: pyba.core.lib.mode.step.Step
   :members:
   :undoc-members:
   :show-inheritance:

DFS (Depth-First Search)
^^^^^^^^^^^^^^^^^^^^^^^^

Entry point for deep exploration mode.

.. autoclass:: pyba.core.lib.mode.DFS.DFS
   :members:
   :undoc-members:
   :show-inheritance:

BFS (Breadth-First Search)
^^^^^^^^^^^^^^^^^^^^^^^^^^

Entry point for wide exploration mode.

.. autoclass:: pyba.core.lib.mode.BFS.BFS
   :members:
   :undoc-members:
   :show-inheritance:

Database
--------

Database Configuration
^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: pyba.database.database.Database
   :members:
   :undoc-members:
   :show-inheritance:

Database Functions
^^^^^^^^^^^^^^^^^^

.. autoclass:: pyba.database.db_funcs.DatabaseFunctions
   :members:
   :undoc-members:
   :show-inheritance:

Core Components
---------------

BaseEngine
^^^^^^^^^^

The base class for all engine modes.

.. autoclass:: pyba.core.lib.mode.base.BaseEngine
   :members:
   :undoc-members:
   :show-inheritance:

Provider
^^^^^^^^

LLM provider selection and configuration.

.. autoclass:: pyba.core.provider.Provider
   :members:
   :undoc-members:
   :show-inheritance:

Agents
------

PlaywrightAgent
^^^^^^^^^^^^^^^

The agent responsible for deciding browser actions.

.. autoclass:: pyba.core.agent.playwright_agent.PlaywrightAgent
   :members:
   :undoc-members:
   :show-inheritance:

PlannerAgent
^^^^^^^^^^^^

The agent for generating exploration plans (DFS/BFS).

.. autoclass:: pyba.core.agent.planner_agent.PlannerAgent
   :members:
   :undoc-members:
   :show-inheritance:

BaseAgent
^^^^^^^^^

Base class for all agents with retry logic.

.. autoclass:: pyba.core.agent.base_agent.BaseAgent
   :members:
   :undoc-members:
   :show-inheritance:

Action System
-------------

PlaywrightActionPerformer
^^^^^^^^^^^^^^^^^^^^^^^^^

Executes browser actions.

.. autoclass:: pyba.core.lib.action.PlaywrightActionPerformer
   :members:
   :undoc-members:
   :show-inheritance:

Data Structures
---------------

PlaywrightAction
^^^^^^^^^^^^^^^^

The DSL for browser actions.

.. autoclass:: pyba.utils.structure.PlaywrightAction
   :members:
   :undoc-members:
   :show-inheritance:

PlaywrightResponse
^^^^^^^^^^^^^^^^^^

Response format from the PlaywrightAgent.

.. autoclass:: pyba.utils.structure.PlaywrightResponse
   :members:
   :undoc-members:
   :show-inheritance:

CleanedDOM
^^^^^^^^^^

Structured representation of page DOM.

.. autoclass:: pyba.utils.structure.CleanedDOM
   :members:
   :undoc-members:
   :show-inheritance:

Login Handlers
--------------

BaseLogin
^^^^^^^^^

Base class for automated login handlers.

.. autoclass:: pyba.core.scripts.login.base.BaseLogin
   :members:
   :undoc-members:
   :show-inheritance:

Code Generation
---------------

CodeGeneration
^^^^^^^^^^^^^^

Generates standalone Playwright scripts.

.. autoclass:: pyba.core.lib.code_generation.CodeGeneration
   :members:
   :undoc-members:
   :show-inheritance:

Dependencies
------------

HandleDependencies
^^^^^^^^^^^^^^^^^^

Manages Playwright browser installation.

.. autoclass:: pyba.core.lib.handle_dependencies.HandleDependencies
   :members:
   :undoc-members:
   :show-inheritance:

Exceptions
----------

.. automodule:: pyba.utils.exceptions
   :members:
   :undoc-members:
   :show-inheritance:

