.. pyba documentation master file, created by
   sphinx-quickstart on Sat Oct 25 10:40:19 2025.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

pyba documentation
==================

PyBA is short for "Python-Browser-Automation". It allows you to enter tasks in natural language and have them be executed on the browser. It is built on top of ``playwright`` and it supports traceviewing optionally.

.. note::
   pyba was specifically built for OSINT purposes.

The main differentiating factors between pyba and others are as follows:

- Performs a depth-first-search and supports retracing of steps
- Generates multiple ``plans`` optionally to achieve a particular task and performs them in parallel
- Perfect for use cases when the task is **not** extremely clear and more exploratory in nature

Features
--------

* ``Trace zip`` file creation to recreate the automation for playwright traceviewer
* ``Logger`` and ``dependency management`` automatically
* Creation of the ``automation script`` in file once successful
* Local and server based ``database creation`` for holding all the actions performed
* ``Stealth mode and config`` heavy files for custom bypass laws
* Quick ``login to social media sites`` without passing credentials to the LLM
* The automation script generatation based on tracked logs for repeatable use and accurate sources
* CLI support for running in ``Terminal`` without a script
* ``Exponential backoff`` and retry for API errors to make the automation more robust

The current software version is ``0.3.0``. While this version is reliable and works very well, the project is still under heavy developement and you can expect newer releases soon!

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   modules
   pyba.core
   pyba.database
   pyba.utils
   usage
   cli
   pyba.core.lib.mode