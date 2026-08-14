# Multi-Agent Mesh & Runtime

AegisMCP extends the Model Context Protocol far beyond simple remote procedure calls.

## AegisAgent

The `AegisAgent` class acts as the brains of your system. You provide it a `ModelProvider` (like Anthropic or OpenAI) and a list of tool names. It autonomously iterates through an execution loop, deciding which tools to call.

## The agent_as_tool Pattern

In a true Enterprise Multi-Agent Mesh, agents need to talk to other agents. AegisMCP allows you to instantly convert an entire `AegisAgent` into a standard MCP tool using the `agent_as_tool` adapter.

This allows a top-level Router Agent to call a "Database Analyst Agent" simply by executing a tool call, seamlessly passing contexts down the tree.
