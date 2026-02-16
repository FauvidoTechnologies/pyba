pyba Documentation
==================

**Tell the AI what to do once. Get a script you can run forever. Works for OSINT and webscraping**

PyBA (Python Browser Automation) uses LLMs to autonomously navigate any website, then exports the session as a standalone Playwright script—no API costs on repeat runs.

.. note::

   PyBA was specifically built for **OSINT** and automated intelligence workflows.

Why PyBA?
---------

Every AI browser agent has the same problem: **you pay for every single run**.

- Run it 100 times? Pay for 100 LLM calls.
- Same task every day? Pay every day.
- The AI figures out the same clicks over and over.

**PyBA is different.** Let the AI figure it out once, then export a deterministic script you own forever.

.. code-block:: python

   from pyba import Engine

   engine = Engine(openai_api_key="sk-...")

   # Step 1: AI navigates autonomously
   engine.sync_run(prompt="Go to Hacker News, click the top story, extract all comments")

   # Step 2: Export as a standalone Playwright script
   engine.generate_code(output_path="hacker_news_scraper.py")

Now run ``python hacker_news_scraper.py`` forever. No AI. No API costs. Just Playwright.

Besides, if you already have free API keys, you're golden.

Key Features
------------

- **Four Exploration Modes**: Normal, Step (interactive step-by-step), DFS (depth-first), and BFS (breadth-first)
- **Code Generation**: Export any successful run as a standalone Python script
- **Trace Files**: Every run generates a Playwright ``trace.zip`` for debugging
- **Stealth Mode**: Anti-fingerprinting, random mouse movements, human-like delays
- **Multi-Provider**: Works with OpenAI, Google VertexAI, or Gemini
- **Low Memory Mode**: Optimized browser settings for resource-constrained environments
- **Database Logging**: Store every action in SQLite, PostgreSQL, or MySQL
- **Platform Logins**: Built-in login handlers for Instagram, Gmail, Facebook

Current Version: **0.3.3**

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   installation
   quickstart

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   guide
   modes
   extraction
   database
   code-generation
   cli
   performance

.. toctree::
   :maxdepth: 2
   :caption: Developer Reference

   architecture
   api
