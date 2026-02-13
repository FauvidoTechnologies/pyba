from sqlalchemy import Column, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class EpisodicMemory(Base):
    """
    Memory for history logs

    Arguments:
            - `session_id`: A unique session ID for the run
            - `actions`: A JSON string array of actions given as output by the model
            - `page_url`: A JSON string array of URLs where actions were performed
            - `action_status`: A JSON string array of booleans indicating success/failure for each action
            - `fail_reason`: A JSON string array of failure reasons (null for successful actions)

    All array fields (actions, page_url, action_status, fail_reason) are parallel arrays -
    the i-th element in each array corresponds to the same action.
    """

    __tablename__ = "EpisodicMemory"

    session_id = Column(Text, primary_key=True)
    actions = Column(Text, nullable=False)
    page_url = Column(Text, nullable=False)
    action_status = Column(
        Text, nullable=False
    )  # JSON array of booleans, e.g., '[true, false, true]'
    fail_reason = Column(
        Text, nullable=True
    )  # JSON array of strings/nulls, e.g., '[null, "timeout", null]'

    def __repr__(self):
        return (
            "EpisodicMemory(session_id: {0}, actions: {1}, page_url: {2}, action_statuses: {3}, fail_reason: {4})"
        ).format(
            self.session_id,
            self.actions,
            self.page_url,
            self.action_status,
            self.fail_reason,
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
            "BFSEpisodicMemory(session_id: {0}, context_id: {1}, actions: {2}, page_url: {3})"
        ).format(self.session_id, self.context_id, self.actions, self.page_url)
