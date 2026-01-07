# Benchmarks

This directory holds code for benchmarking pyba against two major tools in this domain: `browser-use` and `notteai`.

# Structure

The following constants are used:

- Provider: OpenAI (GPT-4.2)
- Prompt: A simple web based task, same for all
- Running using simple quickstart code for all

The following metrics are measured:

- Time taken to finish the task
- Extraction output performed by the task
- Cost of repeating the workflow?
- CPU internals