# PyBA Web Dashboard

A simple web UI for browser automation. This dashboard allows users who aren't comfortable with Python or CLI tools to use PyBA through an intuitive interface.

## Installation

The web UI requires Streamlit. Install it using Poetry:

```bash
# From the project root
poetry install --with web
```

## Running the Dashboard

From the project root directory:

```bash
# Using Poetry
poetry run streamlit run pyba/core/web/streamlit_app.py

# Or if you have streamlit installed globally
streamlit run pyba/core/web/streamlit_app.py
```

The dashboard will open in your browser at `http://localhost:8501`.

## Features

The web dashboard provides all the functionality of the CLI:

### LLM Provider Configuration
- **OpenAI**: Enter your API key
- **Gemini**: Direct API key support (without VertexAI)
- **VertexAI**: Project ID and server location

### Operation Modes
- **Normal**: Standard execution mode
- **DFS (Depth-First Search)**: Exploratory automation that goes deep
- **BFS (Breadth-First Search)**: Exploratory automation that goes wide

### Browser Options
- Headless mode for background execution
- Auto-handle Playwright dependencies
- Random mouse/scroll movements for stealth
- Verbose logging

### Tracing
- Enable trace recording for debugging
- Specify custom trace save directory

### Auto Login
- Configure automatic login for supported sites (Instagram, Gmail, Facebook)
- Requires environment variables to be set (see main documentation)

### Database Configuration
- SQLite, MySQL, or PostgreSQL support
- Automatic script generation from recorded actions

## How It Works

1. Configure your LLM provider in the sidebar
2. Set your preferred browser options
3. Enter your automation task in the main area
4. (Optional) Enable database logging for script generation
5. Click "Start Scan" to begin

Each scan receives a unique ID and runs in the background. You can monitor progress in the Scan History panel.

## Notes

- The browser instance opens on the same computer running the dashboard
- Scans run in background threads, allowing multiple concurrent scans
- All CLI flags are available through the UI
