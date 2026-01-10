import json
import time
from typing import Optional, List

from pyba.database.database import Database
from pyba.database.models import EpisodicMemory, SemanticMemory, BFSEpisodicMemory


class DatabaseFunctions:
    """
    Composition class for the database functions
    """

    def __init__(self, database: Database):
        """
        Args:
            `database`: The database instance for commiting

        If database is none, it doesn't initialise the database session
        """
        if database is None:
            return
        self.database = database
        self.session = self.database.session

    def submit_query_with_retry(self):
        """
        Function to send submit based queries to db
        (such as insert and update or delete), it retries 100 times if
        connection returned an error.

        Args:
            `session`: session to commit

        Returns:
            True if submitted success otherwise False
        """
        if not hasattr(self, "session"):
            return False

        try:
            for _ in range(1, 100):
                try:
                    self.session.commit()
                    return True
                except Exception:
                    time.sleep(0.1)
        except Exception:
            self.session.rollback()
            return False

        self.session.rollback()
        return False

    def push_to_episodic_memory(
        self,
        session_id: str,
        action: str,
        page_url: str,
        action_status: bool,
        fail_reason: str = None,
    ) -> bool:
        """
        Pushes a new action and page_url onto the stack for a given session_id.
        It retrieves the existing record, appends the new values as JSON strings,
        and updates/inserts the record.

        Args:
            `session_id`: The unique session ID.
            `action`: The action string to be pushed.
            `page_url`: The page URL string to be pushed.
            `action_status`: The success or the failure of the current action (True -> Success, False -> Failure)
            `fail_reason`: A string to dictate why a particular action failed (defaults to None in an event of success)

        Returns:
            True if the operation was successful, otherwise False.
        """
        if not hasattr(self, "session"):
            return False
        try:
            memory_record = (
                self.session.query(EpisodicMemory)
                .filter(EpisodicMemory.session_id == session_id)
                .one_or_none()
            )

            if memory_record:
                try:
                    actions_list = json.loads(memory_record.actions)
                    page_url_list = json.loads(memory_record.page_url)
                    action_status_list = json.loads(memory_record.action_status)
                    fail_reason_list = json.loads(memory_record.fail_reason)
                except json.JSONDecodeError:
                    # If stored data is not a valid json, refresh it with a new list
                    actions_list = []
                    page_url_list = []
                    action_status_list = []
                    fail_reason_list = []

                actions_list.append(action)
                page_url_list.append(page_url)
                action_status_list.append(action_status)
                fail_reason_list.append(fail_reason)

                memory_record.actions = json.dumps(actions_list)
                memory_record.page_url = json.dumps(page_url_list)
                memory_record.action_status = json.dumps(action_status_list)
                memory_record.fail_reason = json.dumps(fail_reason_list)

            else:
                new_memory = EpisodicMemory(
                    session_id=session_id,
                    actions=json.dumps([action]),
                    page_url=json.dumps([page_url]),
                    action_status=json.dumps([action_status]),
                    fail_reason=json.dumps([fail_reason]),
                )
                self.session.add(new_memory)

            return self.submit_query_with_retry()

        except Exception:
            self.session.rollback()
            return False
        finally:
            self.session.close()

    def get_episodic_memory_by_session_id(self, session_id: str) -> Optional[EpisodicMemory]:
        """
        Retrieves an episodic memory record by its `session_id`.

        Args:
            `session_id`: The unique session ID to query for.
        Returns:
            An EpisodicMemory object if found, else None.
        """
        # Check if session exists
        if not hasattr(self, "session"):
            return None
        try:
            memory = self.session.get(EpisodicMemory, session_id)
            return memory
        except Exception:
            return None

    def push_to_bfs_episodic_memory(
        self, session_id: str, context_id: str, action: str, page_url: str
    ) -> bool:
        """
        Pushes a new action and page_url for a specific BFS context.
        Creates a new record if the (session_id, context_id) pair doesn't exist,
        otherwise appends to the existing record.

        Note: This function uses a composite primary key of (session_id, context_id) to allow multiple
        browser windows per session.

        Args:
            `session_id`: The parent session ID for the BFS run
            `context_id`: The unique context ID for this browser window
            `action`: The action string to be pushed
            `page_url`: The page URL string to be pushed

        Returns:
            True if the operation was successful, otherwise False.
        """
        if not hasattr(self, "session"):
            return False

        try:
            memory_record = (
                self.session.query(BFSEpisodicMemory)
                .filter(
                    BFSEpisodicMemory.session_id == session_id,
                    BFSEpisodicMemory.context_id == context_id,
                )
                .one_or_none()
            )

            if memory_record:
                try:
                    actions_list = json.loads(memory_record.actions)
                    page_url_list = json.loads(memory_record.page_url)
                except json.JSONDecodeError:
                    actions_list = []
                    page_url_list = []

                actions_list.append(action)
                page_url_list.append(page_url)

                memory_record.actions = json.dumps(actions_list)
                memory_record.page_url = json.dumps(page_url_list)

            else:
                new_memory = BFSEpisodicMemory(
                    session_id=session_id,
                    context_id=context_id,
                    actions=json.dumps([action]),
                    page_url=json.dumps([page_url]),
                )
                self.session.add(new_memory)

            return self.submit_query_with_retry()

        except Exception:
            self.session.rollback()
            return False
        finally:
            self.session.close()

    def get_bfs_episodic_memory_by_context(
        self, session_id: str, context_id: str
    ) -> Optional[BFSEpisodicMemory]:
        """
        Retrieves a specific BFS context's episodic memory. Needs both the session_id and the context_id to retrieve the correct record.

        Args:
            `session_id`: The parent session ID
            `context_id`: The specific context ID to retrieve

        Returns:
            A BFSEpisodicMemory object if found, else None
        """
        if not hasattr(self, "session"):
            return None
        try:
            memory = (
                self.session.query(BFSEpisodicMemory)
                .filter(
                    BFSEpisodicMemory.session_id == session_id,
                    BFSEpisodicMemory.context_id == context_id,
                )
                .one_or_none()
            )
            return memory
        except Exception:
            return None

    def get_all_bfs_contexts_by_session(
        self, session_id: str
    ) -> Optional[List[BFSEpisodicMemory]]:
        """
        Retrieves all BFS context records for a given session.

        Args:
            `session_id`: The parent session ID to query for

        Returns:
            A list of BFSEpisodicMemory objects for all contexts in the session,
            or None if no records found or error occurred.
        """
        if not hasattr(self, "session"):
            return None
        try:
            memories = (
                self.session.query(BFSEpisodicMemory)
                .filter(BFSEpisodicMemory.session_id == session_id)
                .all()
            )
            return memories if memories else None
        except Exception:
            return None

    def push_to_semantic_memory(self, session_id: str, logs: str) -> bool:
        """
        Pushes logs to semantic memory.

        Args:
            `session_id`: The unique session ID
            `logs`: A dump generated by the memory generator

        Returns:
            A boolean to indicate the success or failure of the operation
        """
        print("in here")
        if not hasattr(self, "session"):
            return False

        try:
            # Access the current memory record if it exists
            memory_record = (
                self.session.query(SemanticMemory)
                .filter(SemanticMemory.session_id == session_id)
                .one_or_none()
            )

            if memory_record:
                try:
                    logs_list = json.loads(memory_record.logs)
                except json.JSONDecodeError:
                    logs_list = []

                logs_list.append(logs)

                memory_record.logs = json.dumps(logs_list)

            else:
                new_memory = SemanticMemory(
                    session_id=session_id,
                    logs=json.dumps([logs]),
                )
                self.session.add(new_memory)

            return self.submit_query_with_retry()

        except Exception as e:
            print(f"Hit exception: {e}")
            self.session.rollback()
            return False
        finally:
            self.session.close()

    def get_semantic_memory_by_session_id(self, session_id: str) -> Optional[SemanticMemory]:
        """
        Retrieves all the semantic memory from the database

        Args:
            `session_id`: The unique session ID to query for.
        Returns:
            An EpisodicMemory object if found, else None.
        """
        if not hasattr(self, "session"):
            return None
        try:
            memory = self.session.get(SemanticMemory, session_id)
            return memory
        except Exception:
            return None
