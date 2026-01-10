Code Generation
===============

PyBA's killer feature: export any successful automation as a standalone Playwright script. Run it forever without AI costs.

.. contents::
   :local:
   :depth: 2

Overview
--------

After PyBA completes an automation, you can generate a Python script that:

- Replays the exact same actions
- Uses Playwright directly (no LLM calls)
- Works without PyBA installed
- Runs indefinitely with zero API costs

Requirements
------------

To generate code, you need:

1. A ``Database`` configured (stores the action history)
2. A completed automation run

Basic Usage
-----------

.. code-block:: python

   from pyba import Engine, Database

   # Database is required for code generation
   db = Database(engine="sqlite", name="/tmp/pyba.db")

   engine = Engine(
       openai_api_key="sk-...",
       database=db
   )

   # Run the automation
   engine.sync_run(
       prompt="Go to GitHub trending and get the top repository name"
   )

   # Generate the script
   engine.generate_code(output_path="/tmp/github_trending.py")

Generated Script
----------------

The generated script looks like this:

.. code-block:: python

   import time
   from playwright.sync_api import sync_playwright

   def run_automation():
       with sync_playwright() as p:
           browser = p.chromium.launch(headless=False)
           page = browser.new_page()

           # Step 1: Navigate to GitHub
           page.goto("https://github.com/trending")

           # Step 2: Wait for content
           page.wait_for_selector(".Box-row", timeout=5000)

           # Step 3: Click on first repository
           page.click(".Box-row h2 a")

           time.sleep(3)  # Keep browser open to see result
           browser.close()

   if __name__ == '__main__':
       run_automation()

Running the Generated Script
----------------------------

The script only requires Playwright:

.. code-block:: bash

   # Install Playwright if not already installed
   pip install playwright
   playwright install

   # Run the script
   python /tmp/github_trending.py

No PyBA. No API keys. Just Playwright.

Supported Actions
-----------------

The code generator supports all PyBA actions:

**Navigation:**

- ``page.goto(url)``
- ``page.go_back()``
- ``page.go_forward()``
- ``page.reload()``

**Interactions:**

- ``page.click(selector)``
- ``page.dblclick(selector)``
- ``page.hover(selector)``
- ``page.fill(selector, value)``
- ``page.type(selector, text)``
- ``page.press(selector, key)``
- ``page.check(selector)``
- ``page.uncheck(selector)``
- ``page.select_option(selector, value)``

**Keyboard/Mouse:**

- ``page.keyboard.press(key)``
- ``page.keyboard.type(text)``
- ``page.mouse.move(x, y)``
- ``page.mouse.click(x, y)``
- ``page.mouse.wheel(x, y)``

**Waits:**

- ``page.wait_for_selector(selector)``
- ``page.wait_for_timeout(ms)``

**Utilities:**

- ``page.screenshot(path=...)``
- ``page.evaluate(js_code)``
- File downloads
- Page management

Limitations
-----------

**Dynamic content**: The generated script replays exact selectors. If the site changes, selectors may break.

**No decision making**: The script is deterministic—it can't adapt to different page states like PyBA can.

**Single session**: The script captures one successful path. It doesn't include retry logic or alternatives.

Use Cases
---------

Scheduled Tasks
^^^^^^^^^^^^^^^

.. code-block:: python

   # One-time AI run to figure out the process
   engine.sync_run(prompt="Check my bank balance")
   engine.generate_code(output_path="check_balance.py")

   # Then schedule with cron (no AI needed)
   # 0 9 * * * python /path/to/check_balance.py

Reproducible Scraping
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # AI figures out the scraping flow
   engine.sync_run(
       prompt="Go to Amazon bestsellers, Electronics category, extract top 10 products"
   )
   engine.generate_code(output_path="amazon_bestsellers.py")

   # Run daily without API costs
   # python amazon_bestsellers.py >> products.log

Team Sharing
^^^^^^^^^^^^

Generate scripts once, share with team members who don't have API keys:

.. code-block:: python

   engine.sync_run(prompt="Fill out the weekly report form")
   engine.generate_code(output_path="weekly_report.py")

   # Share weekly_report.py with the team
   # They just need: pip install playwright && playwright install

Workflow
--------

The recommended workflow:

1. **Develop** with PyBA (AI helps figure out the steps)
2. **Test** the automation works correctly
3. **Generate** the script
4. **Run** the script directly for production use
5. **Regenerate** if the target site changes

.. code-block:: python

   from pyba import Engine, Database

   db = Database(engine="sqlite", name="/tmp/pyba.db")
   engine = Engine(openai_api_key="sk-...", database=db, headless=False)

   # Development: watch it work
   result = engine.sync_run(prompt="Your task here")

   if result:  # Success
       engine.generate_code(output_path="production_script.py")
       print("Script generated! Test it with: python production_script.py")

Customizing Generated Scripts
-----------------------------

The generated script is plain Python—feel free to modify it:

.. code-block:: python

   # Add error handling
   try:
       page.click(".submit-button", timeout=5000)
   except Exception as e:
       print(f"Button not found: {e}")
       page.screenshot(path="error.png")

   # Add loops for multiple items
   for i in range(10):
       page.click(f".item-{i}")
       # ... process item

   # Add data extraction
   title = page.text_content("h1")
   print(f"Page title: {title}")

CodeGeneration Class
--------------------

Under the hood, code generation uses the ``CodeGeneration`` class:

.. code-block:: python

   from pyba.core.lib.code_generation import CodeGeneration
   from pyba.database import DatabaseFunctions

   # Manual code generation
   codegen = CodeGeneration(
       session_id="your-session-id",
       output_path="/tmp/script.py",
       database_funcs=db_funcs
   )

   codegen.generate_script()

This is useful if you want to generate scripts from past sessions without re-running the automation.

