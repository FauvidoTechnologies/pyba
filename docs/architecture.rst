Architecture & Code Walkthrough
================================

This guide explains how PyBA works internally. Understanding the architecture will help you contribute, debug issues, or extend the framework.

.. contents::
   :local:
   :depth: 3

High-Level Overview
-------------------

PyBA follows a layered architecture:

.. code-block:: text

   ┌─────────────────────────────────────────────────────────────┐
   │                     User Code / CLI                         │
   └─────────────────────────────────────────────────────────────┘
                              │
                              ▼
   ┌─────────────────────────────────────────────────────────────┐
   │           Entry Points: Engine, Step, DFS, BFS              │
   │                    (pyba/core/main.py)                      │
   │                 (pyba/core/lib/mode/*.py)                   │
   └─────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
   ┌─────────────┐    ┌─────────────┐    ┌─────────────────┐
   │   Provider  │    │   Agents    │    │   BaseEngine    │
   │  (LLM sel.) │    │ (LLM calls) │    │ (shared logic)  │
   └─────────────┘    └─────────────┘    └─────────────────┘
                              │
                              ▼
   ┌─────────────────────────────────────────────────────────────┐
   │                  Action Performer                           │
   │              (pyba/core/lib/action.py)                      │
   │         Executes Playwright commands on browser             │
   └─────────────────────────────────────────────────────────────┘
                              │
                              ▼
   ┌─────────────────────────────────────────────────────────────┐
   │                     Playwright                              │
   │                  (Browser control)                          │
   └─────────────────────────────────────────────────────────────┘

Directory Structure
-------------------

.. code-block:: text

   pyba/
   ├── __init__.py              # Public exports: Engine, Database, Step, DFS, BFS
   ├── config.yaml              # Default configuration
   ├── logger.py                # Logging setup
   ├── version.py               # Version string
   │
   ├── core/                    # Core automation logic
   │   ├── __init__.py          # Exports: Engine, DependencyManager
   │   ├── main.py              # Engine class (main entry point)
   │   ├── provider.py          # LLM provider selection
   │   ├── tracing.py           # Playwright trace handling
   │   │
   │   ├── agent/               # LLM agents
   │   │   ├── base_agent.py    # Base class with retry logic
   │   │   ├── llm_factory.py   # Creates LLM clients
   │   │   ├── playwright_agent.py  # Action decision agent
   │   │   ├── planner_agent.py     # Plan generation (DFS/BFS)
   │   │   └── extraction_agent.py  # Data extraction agent
   │   │
   │   ├── lib/                 # Core libraries
   │   │   ├── action.py        # PlaywrightActionPerformer
   │   │   ├── code_generation.py   # Script export
   │   │   ├── handle_dependencies.py  # Playwright setup
   │   │   └── mode/            # Exploration modes
   │   │       ├── base.py      # BaseEngine (shared logic)
   │   │       ├── step.py      # Step-by-step interactive mode
   │   │       ├── DFS.py       # Depth-first search
   │   │       └── BFS.py       # Breadth-first search
   │   │
   │   ├── helpers/             # Utility helpers
   │   │   ├── jitters.py       # Random mouse/scroll movements
   │   │   └── mem_dsl.py       # Action-to-natural-language DSL and rolling history
   │   │
   │   └── scripts/             # Pre-built scripts
   │       ├── login/           # Auto-login handlers
   │       │   ├── base.py      # BaseLogin class
   │       │   ├── instagram.py
   │       │   ├── facebook.py
   │       │   └── gmail.py
   │       └── extractions/     # DOM extraction
   │           ├── general.py   # Generic extraction
   │           └── youtube_.py  # YouTube-specific
   │
   ├── database/                # Database layer
   │   ├── database.py          # Database class
   │   ├── db_funcs.py          # DatabaseFunctions helper
   │   ├── models.py            # SQLAlchemy models
   │   ├── sqlite.py            # SQLite handler
   │   ├── postgres.py          # PostgreSQL handler
   │   └── mysql.py             # MySQL handler
   │
   ├── utils/                   # Utilities
   │   ├── common.py            # Helper functions
   │   ├── exceptions.py        # Custom exceptions
   │   ├── structure.py         # Pydantic models (DSL)
   │   ├── load_yaml.py         # Config loader
   │   └── prompts/             # LLM prompts
   │       ├── system_prompt.py
   │       ├── general_prompt.py
   │       └── planner_agent_prompt.py
   │
   └── cli/                     # Command-line interface
       ├── cli_entry.py         # Entry point
       └── cli_core/
           ├── arg_parser.py    # Argument parsing
           └── cli_main.py      # CLI logic

Entry Points
------------

pyba/__init__.py
^^^^^^^^^^^^^^^^

The public API. Users import from here:

.. code-block:: python

   from pyba import Engine, Database, Step, DFS, BFS

This file re-exports:

- ``Engine`` from ``pyba.core.main``
- ``Database`` from ``pyba.database``
- ``Step``, ``DFS``, ``BFS`` from ``pyba.core.lib``

The Engine Class
----------------

Location: ``pyba/core/main.py``

The ``Engine`` class is the main entry point for normal mode automation.

**Inheritance:**

.. code-block:: text

   BaseEngine (pyba/core/lib/mode/base.py)
        │
        ├── Engine (pyba/core/main.py)
        ├── Step (pyba/core/lib/mode/step.py)
        ├── DFS (pyba/core/lib/mode/DFS.py)
        └── BFS (pyba/core/lib/mode/BFS.py)

**Key attributes:**

- ``session_id``: Unique identifier for this run
- ``playwright_agent``: The agent that decides actions
- ``mem``: MemDSL instance that accumulates a rolling natural language action history
- ``mode``: "Normal", "STEP", "DFS", or "BFS"
- ``max_depth``: Maximum actions to take

**The run() method flow:**

.. code-block:: text

   1. Launch browser with Stealth
   2. Create browser context (with tracing if enabled)
   3. Open new page
   4. Extract initial DOM
   5. LOOP (up to max_depth times):
      a. Check for automated login
      b. Pass full action history (from MemDSL) to PlaywrightAgent
      c. If action is None → automation complete → get output
      d. Execute action via PlaywrightActionPerformer
      e. Record outcome in MemDSL (success/failure with reason)
      f. If action failed → retry with updated DOM and full history
      g. Log to database (for code generation)
      h. Extract new DOM
   6. Save trace and close browser

BaseEngine
----------

Location: ``pyba/core/lib/mode/base.py``

The ``BaseEngine`` contains shared logic used by all modes:

**Initialization:**

- Sets up the ``Provider`` (LLM selection)
- Creates the ``PlaywrightAgent``
- Creates a ``MemDSL`` instance for rolling action history
- Initializes database functions if provided
- Handles dependency installation

**Key methods:**

``extract_dom()``
^^^^^^^^^^^^^^^^^

Extracts structured data from the current page:

.. code-block:: python

   async def extract_dom(self, page=None):
       # Wait for page to load
       await self.wait_till_loaded(page_obj)

       # Get page content
       page_html = await page_obj.content()
       body_text = await page_obj.inner_text("body")
       elements = await page_obj.query_selector_all(self.combined_selector)

       # Run extraction engine
       extraction_engine = ExtractionEngines(
           html=page_html,
           body_text=body_text,
           elements=elements,
           base_url=base_url,
           page=page_obj,
       )

       cleaned_dom = await extraction_engine.extract_all()
       return cleaned_dom

Returns a ``CleanedDOM`` dataclass with:

- ``hyperlinks``: List of links on page
- ``input_fields``: Fillable form fields
- ``clickable_fields``: Buttons, clickable elements
- ``actual_text``: Visible text content
- ``current_url``: Current page URL

``fetch_action()``
^^^^^^^^^^^^^^^^^^

Gets the next action from the PlaywrightAgent:

.. code-block:: python

   def fetch_action(self, cleaned_dom, user_prompt, action_history, ...):
       action = self.playwright_agent.process_action(
           cleaned_dom=cleaned_dom,
           user_prompt=user_prompt,
           action_history=action_history,
           extraction_format=extraction_format,
           fail_reason=fail_reason,
           action_status=action_status,
       )
       return action

``generate_output()``
^^^^^^^^^^^^^^^^^^^^^

Called when automation is complete (action is None):

.. code-block:: python

   async def generate_output(self, action, cleaned_dom, prompt):
       if action is None or all(value is None for value in vars(action).values()):
           output = self.playwright_agent.get_output(
               cleaned_dom=cleaned_dom.to_dict(),
               user_prompt=prompt
           )
           return output
       return None

The Agent System
----------------

All agents inherit from ``BaseAgent`` which provides:

- Exponential backoff retry logic
- LLM provider handling (OpenAI, VertexAI, Gemini)
- Shared utilities

BaseAgent
^^^^^^^^^

Location: ``pyba/core/agent/base_agent.py``

**Key features:**

- ``calculate_next_time()``: Exponential backoff calculation
- ``handle_openai_execution()``: OpenAI API calls with retries
- ``handle_vertexai_execution()``: VertexAI API calls with retries
- ``handle_gemini_execution()``: Gemini API calls with retries

**Retry logic:**

.. code-block:: python

   while True:
       try:
           response = agent.send_message(prompt)
           break  # Success
       except Exception:
           wait_time = self.calculate_next_time(attempt_number)
           time.sleep(wait_time)
           attempt_number += 1

PlaywrightAgent
^^^^^^^^^^^^^^^

Location: ``pyba/core/agent/playwright_agent.py``

The brain of the operation. Decides what action to take on each page.

**Two main methods:**

1. ``process_action()``: Given DOM and prompt, returns the next action
2. ``get_output()``: Summarizes results when automation completes

**process_action() flow:**

.. code-block:: text

   1. Format prompt with DOM, user instruction, and full action history
   2. Call LLM with PlaywrightResponse schema
   3. Parse response into action object
   4. If extract_info flag is set → trigger ExtractionAgent
   5. Return action

**The prompt includes:**

- Current DOM (hyperlinks, inputs, clickables, text)
- User's original task
- Full action history from MemDSL (every action taken, with success/failure status and failure reasons)

PlannerAgent
^^^^^^^^^^^^

Location: ``pyba/core/agent/planner_agent.py``

Used in DFS and BFS modes to generate high-level plans.

**For DFS**: Generates one detailed plan, then new plans based on progress.

**For BFS**: Generates multiple plans upfront for parallel execution.

.. code-block:: python

   def generate(self, task, old_plan=None):
       prompt = self._initialise_prompt(task=task, old_plan=old_plan)
       return self._call_model(agent=self.agent, prompt=prompt)

ExtractionAgent
^^^^^^^^^^^^^^^

Location: ``pyba/core/agent/extraction_agent.py``

Extracts structured data from pages when requested.

- Runs in a separate thread (non-blocking)
- Uses user-provided Pydantic model or generic format
- Stores results in database

The Action System
-----------------

PlaywrightAction (DSL)
^^^^^^^^^^^^^^^^^^^^^^

Location: ``pyba/utils/structure.py``

Defines all possible browser actions as a Pydantic model:

.. code-block:: python

   class PlaywrightAction(BaseModel):
       # Navigation
       goto: Optional[str]
       go_back: Optional[bool]
       go_forward: Optional[bool]
       reload: Optional[bool]

       # Interactions
       click: Optional[str]
       fill_selector: Optional[str]
       fill_value: Optional[str]
       # ... many more fields

The LLM fills in the relevant fields based on what action to take.

PlaywrightActionPerformer
^^^^^^^^^^^^^^^^^^^^^^^^^

Location: ``pyba/core/lib/action.py``

Executes actions on the browser. Maps action fields to Playwright commands.

**The perform() dispatcher:**

.. code-block:: python

   async def perform(self):
       a = self.action
       if a.goto:
           return await self.handle_navigation()
       if a.click:
           return await self.handle_click()
       if a.fill_selector and a.fill_value is not None:
           return await self.handle_input()
       # ... handles all action types

**Special handling in handle_click():**

- Checks if click target is actually a hyperlink
- Extracts href and navigates directly if so
- Handles strict mode violations (multiple matches)
- Scrolls element into view before clicking

The Provider System
-------------------

Location: ``pyba/core/provider.py``

Detects which LLM provider the user configured:

.. code-block:: python

   class Provider:
       def handle_keys(self):
           if self.openai_api_key:
               self.provider = "openai"
               self.model = "gpt-4o"
           elif self.vertexai_project_id:
               self.provider = "vertexai"
               self.model = "gemini-2.0-flash"
           elif self.gemini_api_key:
               self.provider = "gemini"
               self.model = "gemini-2.5-pro"

LLMFactory
^^^^^^^^^^

Location: ``pyba/core/agent/llm_factory.py``

Creates the actual LLM clients based on provider:

- OpenAI: Uses ``openai.OpenAI()`` client
- VertexAI: Uses ``vertexai`` SDK
- Gemini: Uses ``google.genai`` client

Database Layer
--------------

Location: ``pyba/database/``

**Database class** (``database.py``):

- Creates SQLAlchemy engine
- Initializes tables via handlers
- Supports SQLite, PostgreSQL, MySQL

**DatabaseFunctions** (``db_funcs.py``):

- ``push_to_episodic_memory()``: Log an action
- ``get_episodic_memory_by_session_id()``: Retrieve session logs

**Models** (``models.py``):

.. code-block:: python

   class EpisodicMemory(Base):
       __tablename__ = "EpisodicMemory"

       id = Column(Integer, primary_key=True)
       session_id = Column(String(64))
       actions = Column(Text)      # JSON array
       urls = Column(Text)         # JSON array
       action_status = Column(Boolean)
       fail_reason = Column(Text)

Login System
------------

Location: ``pyba/core/scripts/login/``

**BaseLogin** (``base.py``):

Abstract base class for login handlers:

.. code-block:: python

   class BaseLogin(ABC):
       def __init__(self, page, engine_name):
           self.config = load_config("general")["automated_login_configs"][engine_name]
           self.username = os.getenv(f"{engine_name}_username")
           self.password = os.getenv(f"{engine_name}_password")

       @abstractmethod
       async def _perform_login(self) -> bool:
           raise NotImplementedError

       async def run(self):
           # Check if we're on a login page
           if not verify_login_page(self.page.url, self.config["urls"]):
               return None

           # Perform the login
           success = await self._perform_login()

           # Handle 2FA if needed
           if self.uses_2FA:
               await self._handle_2fa()

           return success

**Site-specific implementations:**

- ``instagram.py``: Instagram login flow
- ``facebook.py``: Facebook login flow
- ``gmail.py``: Gmail login flow

Each uses hardcoded selectors from ``config.yaml`` for speed.

DOM Extraction
--------------

Location: ``pyba/core/scripts/extractions/``

**ExtractionEngines** (``general.py``):

Extracts structured data from raw HTML:

.. code-block:: python

   async def extract_all(self):
       cleaned_dom = CleanedDOM()

       # Extract hyperlinks
       cleaned_dom.hyperlinks = self._extract_hyperlinks()

       # Extract input fields
       cleaned_dom.input_fields = await self._extract_input_fields()

       # Extract clickable elements
       cleaned_dom.clickable_fields = await self._extract_clickables()

       # Get visible text
       cleaned_dom.actual_text = self._extract_text()

       # Special YouTube handling
       if "youtube.com" in self.base_url:
           cleaned_dom.youtube = await youtube_extraction(self.page)

       return cleaned_dom

Code Generation
---------------

Location: ``pyba/core/lib/code_generation.py``

**CodeGeneration class:**

1. Queries database for session actions
2. Parses each action string
3. Maps to Playwright code templates
4. Generates complete Python script

.. code-block:: python

   def generate_script(self):
       actions_list = self._get_run_actions()

       script_header = "from playwright.sync_api import sync_playwright..."
       script_body = []

       for action_str in actions_list:
           code = self._parse_action_to_code(action_str)
           script_body.append(code)

       final_script = script_header + "\n".join(script_body) + script_footer

       with open(self.output_path, "w") as f:
           f.write(final_script)

Stealth & Jitters
-----------------

Location: ``pyba/core/helpers/jitters.py``

**MouseMovements:**

.. code-block:: python

   async def random_movement(self):
       # Generate random bezier curve
       # Move mouse along curve with realistic timing

**ScrollMovements:**

.. code-block:: python

   async def apply_scroll_jitters(self):
       # Small random scrolls during waits
       # Simulates human fidgeting

Used during:

- Page load waits
- Action execution
- 2FA waiting

Execution Flow Diagram
----------------------

**Normal Mode:**

.. code-block:: text

   User calls engine.sync_run(prompt)
         │
         ▼
   Launch browser with Stealth
         │
         ▼
   Create context & page
         │
         ▼
   Extract initial DOM ◄────────────────┐
         │                              │
         ▼                              │
   PlaywrightAgent.process_action()     │
   (receives full action history)       │
         │                              │
         ▼                              │
   Action is None? ───Yes──► get_output() ──► Return result
         │
         No
         │
         ▼
   PlaywrightActionPerformer.perform()
         │
         ▼
   Record action in MemDSL
   (success or failure with reason)
         │
         ▼
   Action failed? ───Yes──► retry_perform_action()
         │                          │
         No                         │
         │                          │
         ▼                          │
   Log to database                  │
   Extract new DOM ─────────────────┘

**Step Mode:**

.. code-block:: text

   User calls step.start()
         │
         ▼
   Launch browser with Stealth
         │
         ▼
   Create context & page
         │
         ▼
   Extract initial DOM
         │
         ▼
   Return control to user
         │
         ▼
   User calls step.step(instruction)
         │
         ▼
   FOR up to max_actions_per_step: ◄──┐
         │                            │
         ▼                            │
   PlaywrightAgent.process_action()   │
         │                            │
         ▼                            │
   Action is None? ───Yes──► Return output to user
         │                            │
         No                           │
         │                            │
         ▼                            │
   PlaywrightActionPerformer          │
         │                            │
         ▼                            │
   Action failed? ───Yes──► Retry     │
         │                            │
         No                           │
         │                            │
         ▼                            │
   Record action in MemDSL             │
   Extract new DOM ───────────────────┘
         │
         ▼
   Return control to user
         │
         ▼
   User calls step.stop()
         │
         ▼
   Save trace & close browser

**DFS Mode:**

.. code-block:: text

   User calls dfs.sync_run(prompt)
         │
         ▼
   Launch browser
         │
         ▼
   FOR each breadth iteration:
         │
         ▼
   PlannerAgent.generate(task, old_plan)
         │
         ▼
   FOR each depth step:
         │
         ▼
      [Same as Normal mode loop]
         │
         ▼
   old_plan = current_plan

**BFS Mode:**

.. code-block:: text

   User calls bfs.sync_run(prompt)
         │
         ▼
   PlannerAgent.generate(task) → List of plans
         │
         ▼
   FOR each plan IN PARALLEL:
         │
         ▼
      Launch separate browser
         │
         ▼
      [Same as Normal mode loop]
         │
         ▼
   Collect all results

Extending PyBA
--------------

Adding a New Login Handler
^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Create ``pyba/core/scripts/login/newsite.py``
2. Inherit from ``BaseLogin``
3. Implement ``_perform_login()``
4. Add to ``pyba/core/scripts/__init__.py``
5. Add selectors to ``config.yaml``

Adding a New Action
^^^^^^^^^^^^^^^^^^^

1. Add field to ``PlaywrightAction`` in ``structure.py``
2. Add handler method in ``PlaywrightActionPerformer``
3. Add to ``perform()`` dispatcher
4. Add a natural language template in ``MemDSL._resolve()``
5. Add to ``CodeGeneration.action_map`` for script export

Adding a New LLM Provider
^^^^^^^^^^^^^^^^^^^^^^^^^

1. Update ``Provider.handle_keys()``
2. Add client creation in ``LLMFactory``
3. Add execution handler in ``BaseAgent``
4. Update ``config.yaml`` with model settings

