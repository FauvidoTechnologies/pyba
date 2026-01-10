Data Extraction
===============

PyBA can extract structured data from web pages during automation. This page covers how to define extraction formats and use them effectively.

.. contents::
   :local:
   :depth: 2

Overview
--------

PyBA extracts data in two ways:

1. **Pydantic Models**: Define exact structure with type hints
2. **Natural Language**: Describe what you want in the prompt

The Pydantic approach is more precise and recommended for production use.

Using Pydantic Models
---------------------

Define a Pydantic ``BaseModel`` to specify exactly what data you want:

.. code-block:: python

   from typing import List, Optional
   from pydantic import BaseModel
   from pyba import Engine, Database

   class HackerNewsPost(BaseModel):
       title: str
       num_upvotes: Optional[int]
       num_comments: Optional[int]
       url: Optional[str]

   database = Database(engine="sqlite", name="/tmp/pyba.db")
   engine = Engine(
       openai_api_key="sk-...",
       database=database,
       enable_tracing=True
   )

   result = engine.sync_run(
       prompt="Go to news.ycombinator.com and extract all posts from the front page",
       extraction_format=HackerNewsPost
   )

**Key points:**

- Use ``Optional`` for fields that might not exist
- The extraction happens **during** navigation, not just at the end
- Data is stored in the database if configured

How Extraction Works
--------------------

When you provide an ``extraction_format``:

1. The **Playwright Agent** decides if the current page contains relevant data
2. If yes, it sets an internal ``extract_info`` flag
3. The **Extraction Agent** runs in a separate thread to extract data
4. Extraction happens without blocking the main automation

This means you get data progressively as PyBA navigates, not just from the final page.

Extraction Agent
^^^^^^^^^^^^^^^^

The Extraction Agent:

- Receives the visible text from the page
- Uses the LLM to extract data matching your Pydantic model
- Stores results in the database

Example: E-commerce Scraping
----------------------------

.. code-block:: python

   from typing import List, Optional
   from pydantic import BaseModel
   from pyba import Engine, Database

   class Product(BaseModel):
       name: str
       price: str
       rating: Optional[str]
       num_reviews: Optional[str]

   db = Database(engine="sqlite", name="/tmp/products.db")
   engine = Engine(openai_api_key="sk-...", database=db)

   result = engine.sync_run(
       prompt="Go to Amazon, search for 'wireless mouse', and extract the first 5 products",
       extraction_format=Product
   )

Example: News Articles
----------------------

.. code-block:: python

   from typing import Optional
   from pydantic import BaseModel
   from pyba import Engine

   class Article(BaseModel):
       headline: str
       author: Optional[str]
       date: Optional[str]
       summary: Optional[str]

   engine = Engine(openai_api_key="sk-...")

   result = engine.sync_run(
       prompt="Go to BBC News and extract the top 3 headlines with their summaries",
       extraction_format=Article
   )

Natural Language Extraction
---------------------------

For quick tasks, you can describe the extraction in your prompt:

.. code-block:: python

   engine = Engine(openai_api_key="sk-...")

   result = engine.sync_run(
       prompt="""
       Go to news.ycombinator.com.
       Extract all posts from the front page.
       For each post, get: title, number of upvotes, number of comments.
       """
   )

This is less precise than Pydantic models but works for simple cases.

Best Practices
--------------

Use Optional Fields
^^^^^^^^^^^^^^^^^^^

Web pages are unpredictable. Use ``Optional`` for fields that might be missing:

.. code-block:: python

   class Product(BaseModel):
       name: str                          # Required - should always exist
       price: Optional[str] = None        # Optional - might be "Price unavailable"
       rating: Optional[float] = None     # Optional - new products might not have ratings

Be Specific in Your Prompt
^^^^^^^^^^^^^^^^^^^^^^^^^^

The extraction quality depends on your prompt. Be specific about:

- What page to visit
- How many items to extract
- What fields matter most

.. code-block:: python

   # Good prompt
   result = engine.sync_run(
       prompt="Go to GitHub trending. Extract the top 10 repositories. For each, get: name, description, stars, and programming language.",
       extraction_format=Repository
   )

   # Vague prompt
   result = engine.sync_run(
       prompt="Get GitHub stuff",
       extraction_format=Repository
   )

Use Database for Persistence
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Extracted data is stored in the database if configured:

.. code-block:: python

   from pyba import Engine, Database

   db = Database(engine="sqlite", name="/tmp/extractions.db")
   engine = Engine(openai_api_key="sk-...", database=db)

   # Data is automatically persisted
   result = engine.sync_run(
       prompt="Extract product data...",
       extraction_format=Product
   )

Limitations
-----------

- **One model per run**: You can only specify one ``extraction_format`` per ``run()`` call
- **Text-based**: Extraction works on visible text, not images or PDFs
- **LLM quality**: Extraction accuracy depends on the LLM's understanding

YouTube Extraction
------------------

PyBA has special handling for YouTube pages. When on YouTube, it uses a custom DOM extraction script optimized for video metadata:

.. code-block:: python

   result = engine.sync_run(
       prompt="Go to this YouTube video and extract: title, views, likes, channel name"
   )

The YouTube extractor pulls:

- Video title and description
- View count and likes
- Channel information
- Comments (if visible)
