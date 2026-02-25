<h1 align="center">PyBA</h1>

<p align="center">
  <strong>Tell the AI what to do once. Get a Python script you can run forever.</strong>
</p>

<p align="center">
  PyBA uses LLMs to autonomously navigate any website, then exports the session as a standalone Playwright script - no API costs on repeat runs.
</p>

<p align="center">
  <a href="https://pepy.tech/projects/py-browser-automation">
    <img height="28px" src="https://static.pepy.tech/personalized-badge/py-browser-automation?period=total&units=INTERNATIONAL_SYSTEM&left_color=BLACK&right_color=GREEN&left_text=downloads" />
  </a>
  &nbsp;&nbsp;
  <a href="https://badge.socket.dev/pypi/package/py-browser-automation/0.2.8?artifact_id=tar-gz">
    <img height="28px" src="https://badge.socket.dev/pypi/package/py-browser-automation/0.2.8?artifact_id=tar-gz" />
  </a>
</p>

<p align="center">
  <a href="https://pypi.org/project/py-browser-automation/"><b>PyPI</b></a> •
  <a href="https://pyba.readthedocs.io/"><b>Documentation</b></a> •
  <a href="https://openhub.net/p/pyba"><b>OpenHub</b></a>
</p>

---

# Pyba

A browser automation software, specialized for OSINT purposes.

### Here's a short demo:

https://github.com/user-attachments/assets/ab258c0d-760d-4994-ada7-6002d46fe8ff

### Part 2:

https://github.com/user-attachments/assets/a34d53af-9896-4435-8778-274ec9f204e3


### Getting the script

```python
from pyba import Engine

engine = Engine(openai_api_key="sk-...")

# Step 1: AI navigates autonomously
engine.sync_run(
    prompt="Go to Hacker News, click the top story, extract all comments"
)

# Step 2: Export as a standalone Playwright script
engine.generate_code(output_path="hacker_news_scraper.py")
```

Now run `python hacker_news_scraper.py` forever. No AI. No API costs.

---

## Installation

```sh
pip install py-browser-automation
```

or via brew

```sh
brew tap fauvidotechnologies/pyba
brew install pyba
```
---

## What Can You Do?

### Automate Repetitive Browser Tasks
```python
engine.sync_run(
    prompt="Login to my bank, download this month's statement as PDF",
    automated_login_sites=["swissbank"]
)
engine.generate_code("download_statement.py")
```

### OSINT & Reconnaissance
```python
from pyba import DFS

dfs = DFS(openai_api_key="sk-...")
dfs.sync_run(
    prompt="Find all social media accounts linked to username 'targetuser123'"
)
```

### Structured Data Extraction
```python
from pydantic import BaseModel

class Product(BaseModel):
    name: str
    price: float
    rating: float

engine.sync_run(
    prompt="Scrape all products from the first 3 pages",
    extraction_format=Product
)
# Data is extracted DURING navigation, stored in your database
```

### Authenticated Workflows
```python
engine.sync_run(
    prompt="Go to my Instagram DMs and message john Paula 'Running 10 mins late'",
    automated_login_sites=["instagram"]
)
# Credentials come from env vars - never exposed to the LLM
```

---

## Four Exploration Modes

| Mode | Use Case | Example |
|------|----------|---------|
| **Normal** | Direct task execution | "Fill out this form and submit" |
| **Step** | Interactive, step-by-step control | "Click here" → "Now search for X" → "Extract that" |
| **DFS** | Deep investigation | "Analyze this GitHub user's contribution patterns" |
| **BFS** | Wide discovery | "Map all pages linked from this homepage" |

```python
from pyba import Engine, Step, DFS, BFS

# Normal mode (default)
engine = Engine(openai_api_key="...")

# Step-by-step interactive mode
step = Step(openai_api_key="...")

# Deep-first exploration
dfs = DFS(openai_api_key="...")

# Breadth-first discovery
bfs = BFS(openai_api_key="...")
```

### Interactive Step-by-Step Automation
```python
from pyba import Step

step = Step(openai_api_key="sk-...")

await step.start()
await step.step("Go to google.com and search for 'playwright python'")
await step.step("Click the first result")
output = await step.step("Extract the installation instructions")
await step.stop()
```

---

## Key Features

### Code Generation
Export any successful run as a standalone Python script. Run it forever without AI.

### Trace Files
Every run generates a Playwright trace.zip — replay exactly what happened in [Trace Viewer](https://trace.playwright.dev/).

### Low Memory Mode
Saves ~120MB of idle RAM by lazy-loading heavy Python dependencies (oxymouse, google-genai, openai). Chromium flags improve container stability. Built for CI servers, containers, and low-spec machines.

```python
engine = Engine(openai_api_key="sk-...", low_memory=True)
```

### Stealth Mode
Anti-fingerprinting, random mouse movements, human-like delays. Bypass common bot detection.

### Multi-Provider
Works with OpenAI, Google VertexAI, or Gemini.

### Database Logging
Store every action in SQLite, PostgreSQL, or MySQL. Audit trails and replay capability.

### Platform Logins
Built-in login handlers for Instagram, Gmail, Facebook. Credentials stay in env vars.

---

## Quick Examples

### Extract YouTube Video Metadata
```python
engine.sync_run(
    prompt="Go to this YouTube video and extract: title, view count, like count, channel name, upload date"
)
```

### Fill a Multi-Page Form
```python
engine.sync_run(
    prompt="Fill out the job application: Name='John Doe', Email='john@email.com', upload resume from ~/resume.pdf, submit"
)
engine.generate_code("job_application.py")  # Replay anytime
```

### Research a Company
```python
dfs = DFS(openai_api_key="...")
dfs.sync_run(
    prompt="Find the leadership team, recent news, and funding history for Acme Corp"
)
```

---


---

## Configuration

```python
from pyba import Engine, Database

# With database logging
db = Database(engine="sqlite", name="runs.db")

engine = Engine(
    openai_api_key="sk-...",
    headless=False,           # Watch it work
    enable_tracing=True,      # Generate trace.zip
    max_depth=20,             # Max actions per run
    database=db               # Log everything
)
```

See [full configuration options](https://pyba.readthedocs.io/) in the docs.

---

## Origin

PyBA was built for automated intelligence and OSINT — replicating everything a human analyst can do in a browser, but with reproducibility and speed.

If you're doing security research, competitive intelligence, or just automating tedious browser tasks, this is for you.

---

## Status

> **v0.3.0** - Active development. First stable release: December 18, 2025.

Breaking changes may occur. Pin your version in production.

---

<p align="center">
  <b>If PyBA saved you time, consider giving it a ⭐</b>
</p>
