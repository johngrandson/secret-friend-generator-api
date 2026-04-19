import src.domain.agents.core.agents_factory as factory_mod
import src.domain.agents.core.agents_swarm as mod
from tests.domain.agents.core.conftest import ToolCapableFakeLLM


def test_make_swarm_returns_invokable(fake_llm: ToolCapableFakeLLM) -> None:
    agent_a = factory_mod.make_agent(name="agent-a", llm=fake_llm)
    agent_b = factory_mod.make_agent(name="agent-b", llm=fake_llm)
    swarm = mod.make_swarm(agents=[agent_a, agent_b], default_active_agent="agent-a")
    assert callable(getattr(swarm, "invoke", None))


def test_make_swarm_single_agent(fake_llm: ToolCapableFakeLLM) -> None:
    agent = factory_mod.make_agent(name="solo", llm=fake_llm)
    swarm = mod.make_swarm(agents=[agent], default_active_agent="solo")
    assert callable(getattr(swarm, "invoke", None))
