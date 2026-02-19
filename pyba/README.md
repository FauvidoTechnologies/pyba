# Directory structure

```
pyba/
├── __init__.py              # Public exports: Engine, Database, Step, DFS, BFS
├── config.yaml              # Default configuration
├── logger.py                # Logging setup
├── version.py               # Version string
│
├── core/                    # Core automation logic
│   ├── main.py              # Engine class (main entry point)
│   ├── provider.py          # LLM provider selection
│   ├── tracing.py           # Playwright trace handling
│   │
│   ├── agent/               # LLM agents
│   │   ├── base_agent.py    # Base class with retry logic
│   │   ├── llm_factory.py   # Creates LLM clients per provider
│   │   ├── playwright_agent.py  # Action decision agent
│   │   ├── planner_agent.py     # Plan generation (DFS/BFS)
│   │   └── extraction_agent.py  # Data extraction agent
│   │
│   ├── lib/                 # Core libraries
│   │   ├── action.py        # PlaywrightActionPerformer
│   │   ├── code_generation.py   # Script export from session logs
│   │   ├── handle_dependencies.py  # Playwright setup
│   │   └── mode/            # Exploration modes
│   │       ├── base.py      # BaseEngine (shared logic, MemDSL init)
│   │       ├── step.py      # Step-by-step interactive mode
│   │       ├── DFS.py       # Depth-first search
│   │       └── BFS.py       # Breadth-first search
│   │
│   ├── helpers/             # Utility helpers
│   │   ├── jitters.py       # Random mouse/scroll movements
│   │   └── mem_dsl.py       # Action-to-natural-language DSL and rolling history
│   │
│   └── scripts/             # Pre-built scripts
│       ├── js/              # Browser-side JavaScript
│       │   ├── extractions.js    # Site-specific link extraction
│       │   └── input_fields.js   # Batch input field discovery
│       ├── login/           # Auto-login handlers
│       │   ├── base.py      # BaseLogin class
│       │   ├── instagram.py
│       │   ├── facebook.py
│       │   └── gmail.py
│       └── extractions/     # DOM extraction engines
│           ├── general.py   # Generic extraction
│           ├── youtube_.py  # YouTube-specific
│           └── wikipedia_.py # Wikipedia-specific
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
│   ├── structure.py         # Pydantic models (PlaywrightAction DSL)
│   ├── load_yaml.py         # Config loader
│   ├── low_memory.py        # Low-memory Chromium flags
│   └── prompts/             # LLM prompts
│       ├── system_prompt.py
│       ├── step_system_prompt.py
│       ├── general_prompt.py
│       ├── output_general_prompt.py
│       ├── output_system_prompt.py
│       ├── planner_agent_prompt.py
│       └── extraction_prompts.py
│
└── cli/                     # Command-line interface
    ├── cli_entry.py         # Entry point
    └── cli_core/
        ├── arg_parser.py    # Argument parsing
        └── cli_main.py      # CLI logic
```
