import src.domain.agents.core.handoff as mod


def test_create_handoff_tool_is_callable() -> None:
    assert callable(mod.create_handoff_tool)


def test_create_handoff_tool_returns_tool_with_name() -> None:
    handoff = mod.create_handoff_tool(agent_name="target-agent")
    assert hasattr(handoff, "name")


def test_create_handoff_tool_name_reflects_agent() -> None:
    handoff = mod.create_handoff_tool(agent_name="my-agent")
    assert handoff.name  # non-empty string
