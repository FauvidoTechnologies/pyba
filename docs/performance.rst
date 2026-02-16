Performance & Benchmarking
==========================

.. contents::
   :local:
   :depth: 2

Performance Tips
-----------------

1. **Use headless mode** for faster execution (``headless=True``)
2. **Enable low memory mode** on resource-constrained environments (``low_memory=True``)
3. **Enable database logging** only when you need code generation
4. **Set appropriate max_depth** — higher isn't always better
5. **Use extraction_format** when you need structured data

Benchmarking Memory
--------------------

You can measure PyBA's memory usage on your own machine using this script:

.. code-block:: python

   import asyncio, os, glob, gc

   def chromium_rss():
       total = 0
       for p in glob.glob("/proc/[0-9]*/stat"):
           try:
               pid = int(p.split("/")[2])
               if b"chromium" in open(f"/proc/{pid}/cmdline", "rb").read().lower():
                   with open(f"/proc/{pid}/statm") as f:
                       total += int(f.read().split()[1])
           except Exception:
               pass
       return total * os.sysconf("SC_PAGE_SIZE") // 1048576

   def py_rss():
       return int(open(f"/proc/{os.getpid()}/statm").read().split()[1]) * os.sysconf("SC_PAGE_SIZE") // 1048576

   async def bench(low_memory):
       from pyba import Step
       print(f"--- low_memory={low_memory} ---")
       print(f"Before: python={py_rss()} MB")
       step = Step(gemini_api_key="...", headless=True, low_memory=low_memory, enable_tracing=False)
       await step.start()
       await step.page.goto("https://www.amazon.com", wait_until="domcontentloaded")
       await asyncio.sleep(5)
       try:
           await step.step("Search for headphones")
       except Exception:
           pass
       print(f"Peak: chromium={chromium_rss()} MB, python={py_rss()} MB")
       await step.stop()
       del step
       gc.collect()
       print(f"After: python={py_rss()} MB")

   asyncio.run(bench(low_memory=True))

Measured Results
^^^^^^^^^^^^^^^^

Tested on Amazon.com, headless mode, Gemini provider:

.. list-table::
   :header-rows: 1

   * - Metric
     - ``low_memory=True``
     - ``low_memory=False``
   * - Idle (before any session)
     - ~60 MB
     - ~180 MB
   * - Peak (during session)
     - ~940 MB
     - ~940 MB
   * - After session cleanup
     - ~130 MB
     - ~130 MB

Where the Savings Are
^^^^^^^^^^^^^^^^^^^^^^

The ~120MB saving is at idle — before any browser session is launched. This comes from lazy-loading
heavy Python dependencies:

- ``oxymouse`` (numpy/scipy): ~46MB
- ``google-genai``: ~64MB (skipped when using OpenAI)
- ``openai``: ~9MB (skipped when using Gemini)

Peak memory during a session is dominated by Chromium (~800MB) which is unaffected by ``low_memory``.
After the first session, lazy-loaded modules remain cached in ``sys.modules`` for the process lifetime.

.. note::

   The Chromium flags in low memory mode (``--disable-gpu``, ``--disable-dev-shm-usage``, etc.) do not
   measurably reduce browser RSS. They improve stability in containerized environments, especially
   ``--disable-dev-shm-usage`` which prevents OOM when ``/dev/shm`` is too small.

Memory Lifecycle in a Server
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you run PyBA as a long-lived server (e.g. with aiohttp), the memory lifecycle is:

1. **Server starts**: ~60MB (with ``low_memory=True``) or ~180MB (without)
2. **First session opens**: Jumps to ~600-1000MB (Chromium + lazy-loaded modules)
3. **First session closes**: Drops to ~130-220MB (modules stay loaded, Chromium exits)
4. **Subsequent sessions**: Same peak, returns to ~130-220MB each time

To ensure memory is returned to the OS after sessions close, set these environment variables
in your container:

.. code-block:: bash

   MALLOC_TRIM_THRESHOLD_=65536
   MALLOC_MMAP_THRESHOLD_=65536

These tell glibc's allocator to return freed pages to the OS more aggressively.
