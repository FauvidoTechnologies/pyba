__all__ = ["Engine", "Database", "DFS", "BFS", "Step"]


def __getattr__(name):
    if name == "Engine":
        from pyba.core import Engine

        return Engine
    if name == "Database":
        from pyba.database import Database

        return Database
    if name in ("DFS", "BFS", "Step"):
        from pyba.core.lib import DFS, BFS, Step

        return {"DFS": DFS, "BFS": BFS, "Step": Step}[name]
    raise AttributeError(f"module 'pyba' has no attribute {name!r}")
