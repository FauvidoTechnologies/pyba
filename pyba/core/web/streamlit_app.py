import threading
import uuid
from datetime import datetime
from pathlib import Path

import streamlit as st

from pyba import Engine, Database
from pyba.core.lib import DFS, BFS

if "SCAN_STORE" not in dir():
    SCAN_STORE = {}
    SCAN_LOCK = threading.Lock()


def load_css():
    css_dir = Path(__file__).parent / "static"
    css_file = css_dir / "static.css"
    if css_file.exists():
        css = css_file.read_text()
        st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)


st.set_page_config(
    page_title="PyBA Dashboard",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_css()


def get_scans():
    global SCAN_STORE
    with SCAN_LOCK:
        return dict(SCAN_STORE)


def update_scan(scan_id: str, **kwargs):
    global SCAN_STORE
    with SCAN_LOCK:
        if scan_id in SCAN_STORE:
            SCAN_STORE[scan_id].update(kwargs)


def create_scan(scan_id: str, data: dict):
    global SCAN_STORE
    with SCAN_LOCK:
        SCAN_STORE[scan_id] = data


def run_scan_in_thread(scan_id: str, config: dict):
    try:
        update_scan(scan_id, status="running")

        engine_configs = {
            "openai_api_key": config.get("openai_api_key") or None,
            "vertexai_project_id": config.get("vertexai_project_id") or None,
            "vertexai_server_location": config.get("vertexai_server_location") or None,
            "gemini_api_key": config.get("gemini_api_key") or None,
            "headless": config.get("headless", False),
            "handle_dependencies": config.get("handle_dependencies", False),
            "use_random": config.get("use_random", False),
            "use_logger": config.get("use_logger", True),
            "enable_tracing": config.get("enable_tracing", False),
            "trace_save_directory": config.get("trace_save_directory") or None,
        }

        if config.get("use_database"):
            db_configs = {
                "engine": config.get("database_engine"),
                "name": config.get("database_name"),
                "username": config.get("database_username") or None,
                "password": config.get("database_password") or None,
                "host": config.get("database_host") or None,
                "port": config.get("database_port") or None,
                "ssl_mode": config.get("postgres_ssl_mode", "disabled"),
            }
            engine_configs["database"] = Database(**db_configs)

        operation_mode = config.get("operation_mode", "Normal")

        if operation_mode in {"DFS", "BFS"}:
            engine_configs["max_depth"] = int(config.get("max_depth", 5))
            engine_configs["max_breadth"] = int(config.get("max_breadth", 5))

        if operation_mode == "BFS":
            engine = BFS(**engine_configs)
        elif operation_mode == "DFS":
            engine = DFS(**engine_configs)
        else:
            engine = Engine(**engine_configs)

        task = config.get("task")
        automated_login_sites = config.get("automated_login_sites") or None

        result = engine.sync_run(task, automated_login_sites=automated_login_sites)

        code_output_path = None
        if config.get("generate_code") and config.get("use_database"):
            code_output_path = config.get("code_output_path") or "/tmp/pyba_script.py"
            engine.generate_code(output_path=code_output_path)

        update_scan(
            scan_id,
            status="completed",
            result=result,
            code_output_path=code_output_path,
            completed_at=datetime.now().isoformat(),
        )

    except Exception as e:
        update_scan(
            scan_id,
            status="failed",
            error=str(e),
            completed_at=datetime.now().isoformat(),
        )


def submit_scan(config: dict) -> str:
    scan_id = uuid.uuid4().hex[:12]

    create_scan(
        scan_id,
        {
            "status": "pending",
            "task": config.get("task"),
            "config": config,
            "started_at": datetime.now().isoformat(),
            "result": None,
            "error": None,
        },
    )

    thread = threading.Thread(target=run_scan_in_thread, args=(scan_id, config), daemon=True)
    thread.start()

    return scan_id


# UI Components


def render_sidebar():
    with st.sidebar:
        st.markdown("## Configuration")
        st.markdown("---")

        st.markdown("### LLM Provider")

        provider = st.selectbox(
            "Select Provider",
            ["OpenAI", "Gemini (API Key)", "VertexAI"],
            help="Choose the LLM provider for automation",
        )

        llm_config = {}

        if provider == "OpenAI":
            llm_config["openai_api_key"] = st.text_input(
                "OpenAI API Key", type="password", placeholder="sk-..."
            )
        elif provider == "Gemini (API Key)":
            llm_config["gemini_api_key"] = st.text_input(
                "Gemini API Key", type="password", placeholder="Your Gemini API key"
            )
        else:  # VertexAI
            llm_config["vertexai_project_id"] = st.text_input(
                "Project ID", placeholder="your-project-id"
            )
            llm_config["vertexai_server_location"] = st.text_input(
                "Server Location", placeholder="us-central1"
            )

        st.markdown("---")

        st.markdown("### Operation Mode")
        operation_mode = st.selectbox(
            "Mode",
            ["Normal", "DFS", "BFS"],
            help="Normal: Standard execution | DFS: Depth-first exploration | BFS: Breadth-first exploration",
        )

        exploration_config = {"operation_mode": operation_mode}

        if operation_mode in {"DFS", "BFS"}:
            col1, col2 = st.columns(2)
            with col1:
                exploration_config["max_depth"] = st.number_input(
                    "Max Depth", min_value=1, max_value=50, value=5
                )
            with col2:
                exploration_config["max_breadth"] = st.number_input(
                    "Max Breadth", min_value=1, max_value=50, value=5
                )

        st.markdown("---")

        st.markdown("### Browser Options")

        browser_config = {}
        browser_config["headless"] = st.checkbox(
            "Headless Mode", value=False, help="Run browser without GUI"
        )
        browser_config["handle_dependencies"] = st.checkbox(
            "Auto-handle Dependencies",
            value=False,
            help="Automatically install Playwright dependencies",
        )
        browser_config["use_random"] = st.checkbox(
            "Random Movements", value=False, help="Use random mouse/scroll movements"
        )
        browser_config["use_logger"] = st.checkbox(
            "Verbose Logging", value=True, help="Enable detailed logging"
        )

        st.markdown("---")

        st.markdown("### Tracing")
        browser_config["enable_tracing"] = st.checkbox(
            "Enable Tracing", value=False, help="Create trace files for debugging"
        )

        if browser_config["enable_tracing"]:
            browser_config["trace_save_directory"] = st.text_input(
                "Trace Directory", placeholder="/tmp/traces"
            )

        st.markdown("---")

        st.markdown("### Auto Login")
        login_sites_input = st.text_input(
            "Login Sites",
            placeholder="instagram, gmail, facebook",
            help="Comma-separated list of sites for auto-login",
        )

        login_config = {}
        if login_sites_input.strip():
            login_config["automated_login_sites"] = [
                s.strip() for s in login_sites_input.split(",") if s.strip()
            ]

        return {**llm_config, **exploration_config, **browser_config, **login_config}


def render_database_section():
    with st.expander("Database Configuration (Optional)", expanded=False):
        use_database = st.checkbox("Enable Database Logging", value=False)

        db_config = {"use_database": use_database}

        if use_database:
            col1, col2 = st.columns(2)

            with col1:
                db_config["database_engine"] = st.selectbox(
                    "Database Engine", ["sqlite", "mysql", "postgres"]
                )

                if db_config["database_engine"] == "sqlite":
                    db_config["database_name"] = st.text_input(
                        "Database Path", placeholder="/path/to/database.db"
                    )
                else:
                    db_config["database_name"] = st.text_input(
                        "Database Name", placeholder="pyba_db"
                    )
                    db_config["database_username"] = st.text_input("Username", placeholder="root")
                    db_config["database_password"] = st.text_input(
                        "Password", type="password", placeholder="password"
                    )

            with col2:
                if db_config["database_engine"] != "sqlite":
                    db_config["database_host"] = st.text_input("Host", placeholder="localhost")
                    db_config["database_port"] = st.text_input("Port", placeholder="3306")

                    if db_config["database_engine"] == "postgres":
                        db_config["postgres_ssl_mode"] = st.selectbox(
                            "SSL Mode", ["disabled", "required"]
                        )

            st.markdown("---")

            db_config["generate_code"] = st.checkbox(
                "Generate Automation Script",
                value=False,
                help="Generate a Python script from recorded actions",
            )

            if db_config["generate_code"]:
                db_config["code_output_path"] = st.text_input(
                    "Script Output Path", placeholder="/tmp/pyba_script.py"
                )

        return db_config


def render_scan_card(scan_id: str, scan_data: dict):
    status = scan_data["status"]
    status_class = f"status-{status}"

    st.markdown(
        f"""
        <div class="scan-card">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.75rem;">
                <span class="scan-id">ID: {scan_id}</span>
                <span class="{status_class}">{status.upper()}</span>
            </div>
            <p style="margin: 0.5rem 0; font-size: 0.95rem;">{scan_data['task'][:100]}{'...' if len(scan_data['task']) > 100 else ''}</p>
            <p style="font-size: 0.8rem; margin: 0;">Started: {scan_data['started_at']}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if status == "completed" and scan_data.get("result"):
        with st.expander("View Result"):
            st.write(scan_data["result"])

    if status == "failed" and scan_data.get("error"):
        with st.expander("View Error"):
            st.error(scan_data["error"])


def render_metrics():
    scans = get_scans()

    total = len(scans)
    running = sum(1 for s in scans.values() if s["status"] == "running")
    completed = sum(1 for s in scans.values() if s["status"] == "completed")
    failed = sum(1 for s in scans.values() if s["status"] == "failed")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{total}</div>
                <div class="metric-label">Total Scans</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col2:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{running}</div>
                <div class="metric-label">Running</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col3:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{completed}</div>
                <div class="metric-label">Completed</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col4:
        st.markdown(
            f"""
            <div class="metric-card">
                <div class="metric-value">{failed}</div>
                <div class="metric-label">Failed</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def main():
    """Main application entry point"""
    # Get sidebar configuration
    sidebar_config = render_sidebar()

    # Main content area
    st.markdown("# PyBA Dashboard")
    st.markdown("Browser automation made simple")

    render_metrics()

    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns([1.2, 1])

    with col_left:
        st.markdown("### New Scan")

        task = st.text_area(
            "Automation Task",
            placeholder="Describe what you want to automate...\n\nExample: Go to hackernews.com and extract the top 10 post titles and their upvote counts.",
            height=150,
        )

        db_config = render_database_section()

        if st.button("Start Scan", use_container_width=True):
            if not task.strip():
                st.error("Please enter a task to automate!")
            else:
                full_config = {**sidebar_config, **db_config, "task": task}

                has_llm = any(
                    [
                        full_config.get("openai_api_key"),
                        full_config.get("gemini_api_key"),
                        (
                            full_config.get("vertexai_project_id")
                            and full_config.get("vertexai_server_location")
                        ),
                    ]
                )

                if not has_llm:
                    st.error("Please configure an LLM provider in the sidebar!")
                else:
                    scan_id = submit_scan(full_config)
                    st.success(f"Scan submitted! ID: `{scan_id}`")
                    st.rerun()

    with col_right:
        st.markdown("### Scan History")

        scans = get_scans()

        if not scans:
            st.markdown("No scans yet. Start your first scan!")
        else:
            for scan_id in reversed(list(scans.keys())):
                render_scan_card(scan_id, scans[scan_id])

        if any(s["status"] == "running" for s in scans.values()):
            st.markdown("Auto-refreshing...")
            import time

            time.sleep(2)
            st.rerun()

    st.markdown("---")
    st.markdown("PyBA - Python Browser Automation | [Documentation](https://pyba.readthedocs.io)")


if __name__ == "__main__":
    main()
