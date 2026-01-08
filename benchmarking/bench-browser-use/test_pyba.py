from pyba import Engine

engine = Engine(
    vertexai_project_id="atlas-467316",
    vertexai_server_location="us-central1",
    use_logger=True,
    enable_tracing=True,
    trace_save_directory="/home/purge/Desktop",
    handle_dependencies=False,
    headless=False,
)

output = engine.sync_run(
    "Open Hacker News (news.ycombinator.com) and extract all post titles on the front page."
)

print(output)
