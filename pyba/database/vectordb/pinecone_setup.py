import os
import time
import uuid
from typing import Literal, List

from pinecone import ServerlessSpec
from pinecone.grpc import PineconeGRPC as Pinecone


class Memory:
    def __init__(self, memory_type: Literal["pyba-sm-mem"]):
        self.memory_type = memory_type

        self.pinecone_api_key = os.getenv("pinecone_api_key")
        self.pc = Pinecone(api_key=self.pinecone_api_key)
        self.index = self.create_index(self.memory_type)

        # We use a model hosted by Pinecone.
        # 'multilingual-e5-large' uses 1024 dimensions so we don't have to change the dimensions
        self.model_name = "multilingual-e5-large"
        self.session_id = uuid.uuid4().hex

    def create_index(self, memory_type: str):
        """
        helper function to create indices for each memory structure
        """
        # if not already created
        if self.memory_type not in [idx["name"] for idx in self.pc.list_indexes()]:
            self.pc.create_index(
                name=self.memory_type,
                dimension=1024,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region="us-east-1"),
            )

        while not self.pc.describe_index(self.memory_type).status["ready"]:
            time.sleep(1)

        return self.pc.Index(self.memory_type)

    def embed(self, text: str) -> List:
        """
        Creates an embedding for a given text.
        """
        # Pinecone expects a list of strings, we send one.
        res = self.pc.inference.embed(
            model=self.model_name, inputs=[text], parameters={"input_type": "passage"}
        )
        return res[0].values

    def save(
        self,
        text: str,
        role: Literal["user", "azno"],
        turn_id: int,
    ) -> bool:
        """
        Save a single conversational unit to Pinecone.

        Args:
            `text`: The actual text to be saved
            `role`: A role assignment for the text
            `turn_id`: A unique ID for the current turn of chats

        Usage:
        ```python3
            turn_id = uuid.uuid4().hex
            await self.mem.save(user_text, role="user", turn_id=turn_id)
            await self.mem.save(azno_text, role="azno", turn_id=turn_id)
        ```
        """

        embedding = self.embed(text)
        vector_id = f"{self.session_id}-{turn_id}-{role}"

        vector = {
            "id": vector_id,
            "values": embedding,
            "metadata": {
                "role": role,
                "turn_id": turn_id,
                "preview": text[:300],  # short, safe metadata
            },
        }

        try:
            self.index.upsert(
                vectors=[vector],
                namespace=self.session_id,
            )
            return True

        except Exception as e:
            print(f"Failed to insert vector: {e}")
            return False

    def query(self, query_text: str, top_k: int = 5) -> list:
        """
        Retrieve semantically similar past conversation units
        within the same session.

        Args:
            `query_text`: The text being used to query the DB
            `top_k`: Number of matches to return

        Usage:
            - Combine the last two messages of the user INCLUDING the current one as the `query_text`
        """

        query_embedding = self.embed(query_text)

        try:
            res = self.index.query(
                vector=query_embedding,
                top_k=top_k,
                include_metadata=True,
                namespace=self.session_id,
            )
            results = []
            for match in res.get("matches", []):
                results.append(
                    {
                        "id": match["id"],
                        "score": match["score"],
                        "role": match["metadata"]["role"],
                        "turn_id": match["metadata"]["turn_id"],
                        "preview": match["metadata"]["preview"],
                    }
                )

            return results

        except Exception as e:
            print(f"Query failed: {e}")
            return []


# Future implementation ideas for the vector DB
# Store the raw logs in a SQL based database. Then every ~10-20 turns, store the ENTIRE SUMMARISED
# history in the database.
# We'll see about that, I also need to make the layer on top of this.

# if __name__ == "__main__":
#     mem = Memory(memory_type="azno-ep-mem")
#     a = mem.query("Hello")
#     print(a)
