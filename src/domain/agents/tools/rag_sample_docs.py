"""Sample documents about LangGraph multi-agent concepts for RAG demonstrations."""

SAMPLE_DOCS: list[str] = [
    (
        "LangGraph is a library for building stateful, multi-actor applications with "
        "large language models. It extends LangChain by introducing a graph-based "
        "execution model where nodes represent processing steps and edges define the "
        "flow of data between them. LangGraph supports cycles, branching, and "
        "persistence, making it well-suited for agentic workflows that require "
        "iterative reasoning, tool use, and dynamic decision-making across multiple "
        "steps."
    ),
    (
        "Retrieval-Augmented Generation (RAG) is a technique that enhances language "
        "model responses by retrieving relevant documents from an external knowledge "
        "base before generating an answer. A RAG pipeline typically consists of an "
        "ingestion phase—where documents are chunked, embedded, and stored in a "
        "vector store—and a retrieval phase where a query is embedded and compared "
        "against stored vectors using cosine similarity to find the most relevant "
        "chunks, which are then injected into the model's context window."
    ),
    (
        "The supervisor pattern in multi-agent systems uses a central orchestrator "
        "agent to coordinate a team of specialised sub-agents. The supervisor "
        "receives a user request, decides which sub-agent to invoke next based on "
        "the current state, and routes the output back until the task is complete. "
        "LangGraph's langgraph-supervisor package provides a prebuilt "
        "create_supervisor helper that wires up this pattern with tool-calling so "
        "each sub-agent is exposed as a callable tool to the supervisor LLM."
    ),
    (
        "The swarm pattern is a decentralised multi-agent architecture where agents "
        "hand off control directly to one another without a central coordinator. "
        "Each agent decides autonomously which peer to transfer to next using "
        "handoff tools. LangGraph's langgraph-swarm package implements this with "
        "create_handoff_tool and create_swarm, maintaining a shared message history "
        "and an active_agent field in state so each agent always knows which agent "
        "is currently active."
    ),
    (
        "Human-in-the-loop (HITL) is a design pattern where a human can review, "
        "approve, or modify an agent's actions before execution continues. In "
        "LangGraph this is implemented via interrupt() calls inside graph nodes, "
        "which pause execution and surface a Command to the caller. The graph "
        "persists its state using a checkpointer so that when the human provides "
        "feedback the run can be resumed from exactly the interrupted point without "
        "losing prior context."
    ),
    (
        "The Model Context Protocol (MCP) is an open standard that allows language "
        "models to interact with external tools and data sources through a "
        "well-defined interface. LangChain's langchain-mcp-adapters library bridges "
        "MCP servers and LangChain tools, letting LangGraph agents consume any "
        "MCP-compliant server as a set of callable tools. This enables a rich "
        "ecosystem of plug-and-play integrations—file systems, databases, APIs—that "
        "agents can use without custom glue code."
    ),
]
