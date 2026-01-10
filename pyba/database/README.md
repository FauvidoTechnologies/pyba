# Database

The following databases are implemented:

- [x] Episodic memory in a SQL database (These are raw logs with indications for which actions were a success and which weren't)
- [x] Semantic memory in a vectorDB (These are logs to learn from mistakes, know what to do when you tried at something and it didn't work, see if it has happened before ever)
- [x] Extracted memory in a SQL database (These are extracted data, stored as is)

The semantic memory is a special type because it's going to tell the model what had worked before and what hadn't. Now the way this is being done matters a lot. There are a few questions to ask:

1. How do we decide when to add a datapoint to the semantic memory
2. How do we query the semantic memory (what text do we use to query it?)

The questions will be answered at runtime.