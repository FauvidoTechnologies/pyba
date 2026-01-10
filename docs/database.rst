Database Configuration
======================

PyBA can log all actions to a database, enabling code generation, auditing, and replay capabilities.

.. contents::
   :local:
   :depth: 2

Overview
--------

The database stores:

- **Session information**: Unique IDs for each automation run
- **Actions**: Every action taken during automation
- **Page URLs**: Where each action was performed
- **Status**: Success/failure of each action
- **Extraction results**: Data extracted during automation

Supported Databases
-------------------

PyBA supports three database engines:

+------------+-------------+------------------------+
| Engine     | Type        | Best For               |
+============+=============+========================+
| SQLite     | File-based  | Local development      |
+------------+-------------+------------------------+
| PostgreSQL | Server      | Production, teams      |
+------------+-------------+------------------------+
| MySQL      | Server      | Production, teams      |
+------------+-------------+------------------------+

SQLite Setup
------------

The simplest option—no server required:

.. code-block:: python

   from pyba import Engine, Database

   database = Database(
       engine="sqlite",
       name="/tmp/pyba.db"  # Path to the database file
   )

   engine = Engine(
       openai_api_key="sk-...",
       database=database
   )

The database file is created automatically if it doesn't exist.

PostgreSQL Setup
----------------

For production environments:

.. code-block:: python

   from pyba import Engine, Database

   database = Database(
       engine="postgres",
       name="pyba_db",           # Database name
       host="localhost",         # Or your server IP
       port=5432,                # Default PostgreSQL port
       username="your_user",
       password="your_password",
       ssl_mode="disable"        # Or "require" for encrypted connections
   )

   engine = Engine(
       openai_api_key="sk-...",
       database=database
   )

**SSL Mode options:**

- ``"disable"`` - No encryption (local development)
- ``"require"`` - Encrypted connection (production)

MySQL Setup
-----------

.. code-block:: python

   from pyba import Engine, Database

   database = Database(
       engine="mysql",
       name="pyba_db",           # Database name
       host="localhost",         # Or your server IP
       port=3306,                # Default MySQL port
       username="your_user",
       password="your_password"
   )

   engine = Engine(
       openai_api_key="sk-...",
       database=database
   )

Database Schema
---------------

PyBA creates an ``EpisodicMemory`` table to store automation logs:

.. code-block:: sql

   CREATE TABLE EpisodicMemory (
       id INTEGER PRIMARY KEY,
       session_id VARCHAR(64),
       actions TEXT,              -- JSON array of actions
       urls TEXT,                 -- JSON array of URLs
       action_status BOOLEAN,     -- Success/failure
       fail_reason TEXT           -- Error message if failed
   );

For BFS mode, there's an additional ``BFSEpisodicMemory`` table with a ``context_id`` field to track parallel browser sessions.

Querying the Database
---------------------

SQLite Example
^^^^^^^^^^^^^^

.. code-block:: bash

   sqlite3 /tmp/pyba.db

   # List tables
   .tables

   # View all sessions
   SELECT DISTINCT session_id FROM EpisodicMemory;

   # View actions for a session
   SELECT * FROM EpisodicMemory WHERE session_id = 'your-session-id';

Python Example
^^^^^^^^^^^^^^

.. code-block:: python

   from pyba.database import DatabaseFunctions

   # After running automation with a database
   db_funcs = DatabaseFunctions(database)

   # Get logs for a session
   logs = db_funcs.get_episodic_memory_by_session_id(session_id="your-session-id")

   print(logs.actions)  # JSON string of actions
   print(logs.urls)     # JSON string of URLs

Code Generation
---------------

The main reason to use a database: generating reusable scripts.

.. code-block:: python

   from pyba import Engine, Database

   db = Database(engine="sqlite", name="/tmp/pyba.db")
   engine = Engine(openai_api_key="sk-...", database=db)

   # Run the automation
   engine.sync_run(prompt="Go to example.com and fill the contact form")

   # Generate a standalone script
   engine.generate_code(output_path="/tmp/contact_form.py")

The generated script:

- Uses ``playwright.sync_api`` directly
- Replays the exact actions from the database
- Has no AI dependencies—runs forever without API costs

See :doc:`code-generation` for more details.

Configuration via YAML
----------------------

You can also configure database defaults in ``pyba/config.yaml``:

.. code-block:: yaml

   database:
     engine: "sqlite"
     name: "/tmp/pyba.db"
     host: "localhost"
     port: 5432
     username: ""
     password: ""
     ssl_mode: "disable"

These serve as fallbacks when parameters aren't provided to the ``Database`` constructor.

Best Practices
--------------

Security
^^^^^^^^

**Never** put passwords directly in code:

.. code-block:: python

   import os

   database = Database(
       engine="postgres",
       name="pyba_db",
       host=os.environ["DB_HOST"],
       username=os.environ["DB_USER"],
       password=os.environ["DB_PASSWORD"],
   )

File Paths
^^^^^^^^^^

For SQLite, use absolute paths to avoid confusion:

.. code-block:: python

   # Good
   database = Database(engine="sqlite", name="/tmp/pyba/runs.db")

   # Risky - depends on working directory
   database = Database(engine="sqlite", name="runs.db")

Session Management
^^^^^^^^^^^^^^^^^^

Each ``Engine`` run gets a unique ``session_id``. You can access it:

.. code-block:: python

   engine.sync_run(prompt="Your task")
   print(f"Session ID: {engine.session_id}")

Use this ID to query logs or generate code for specific runs.

Cleanup
^^^^^^^

Database files grow over time. Periodically clean up old sessions:

.. code-block:: sql

   -- SQLite: Delete sessions older than 7 days
   DELETE FROM EpisodicMemory
   WHERE session_id IN (
       SELECT DISTINCT session_id
       FROM EpisodicMemory
       GROUP BY session_id
       HAVING MAX(id) < (SELECT MAX(id) - 1000 FROM EpisodicMemory)
   );

