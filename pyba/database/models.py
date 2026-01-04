from sqlalchemy import Column, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class EpisodicMemory(Base):
    """
    Memory for history logs

    Arguments:
            - `session_id`: A unique session ID for the run
            - `actions`: A JSON string of actions given as output by the model
            - `page_url`: The URL where this action was performed
            - `context_id`: A unique ID generated for each context in BFS

    The `context_id` is a nullable field because it only comes in handy for BFS mode
    """

    __tablename__ = "EpisodicMemory"

    session_id = Column(Text, primary_key=True)
    actions = Column(Text, nullable=False)
    page_url = Column(Text, nullable=False)

    def __repr__(self):
        return ("EpisodicMemory(session_id: {0}, actions: {1}, page_url: {2})").format(
            self.session_id, self.actions, self.page_url
        )


class SemanticMemory(Base):
    """
    Memory for holding intermediate data, relevant goals, extracted outputs

    Arguments:
            - `session_id`: A unique session ID for the run
            - `logs`: The actual logs implemented as a growing buffer

    This is a growing memory type for each session, it holds everything of relevance to the task. This memory
    will be used to summarise the final output type.

    TODO: Update this function for BFS support
    """

    __tablename__ = "SemanticMemory"

    session_id = Column(Text, primary_key=True)
    logs = Column(Text, nullable=False)

    def __repr__(self):
        return ("ExtractedData(session_id: {0}, logs: {1})").format(self.session_id, self.logs)


class BFSEpisodicMemory(Base):
    """
    Memory table specifically for BFS (Breadth-First Search) mode browser sessions.

    This uses a composite primary key of (session_id, context_id) to allow multiple
    browser contexts per session.
    Arguments:
        - `session_id`: The parent session ID that spawned these BFS contexts
        - `context_id`: A unique ID for each browser context within the session
        - `actions`: A JSON string of actions performed in this context
        - `page_url`: A JSON string of URLs visited in this context

    Each (session_id, context_id) pair represents a unique browser context's
    event log within a BFS exploration session.
    """

    __tablename__ = "BFSEpisodicMemory"

    # Composite primary key: allows multiple contexts per session
    session_id = Column(Text, primary_key=True)
    context_id = Column(Text, primary_key=True)
    actions = Column(Text, nullable=False)
    page_url = Column(Text, nullable=False)

    def __repr__(self):
        return (
            "BFSEpisodicMemory(session_id: {0}, context_id: {1}, " "actions: {2}, page_url: {3})"
        ).format(self.session_id, self.context_id, self.actions, self.page_url)
