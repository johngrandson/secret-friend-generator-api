import src.domain.agents.core.agents_factory as factory_mod
import src.domain.agents.core.agents_supervisor as mod
from tests.domain.agents.core.conftest import ToolCapableFakeLLM


def test_make_supervisor_returns_invokable(fake_llm: ToolCapableFakeLLM) -> None:
    worker = factory_mod.make_agent(name="worker", llm=fake_llm)
    supervisor = mod.make_supervisor(agents=[worker], llm=fake_llm)
    assert callable(getattr(supervisor, "invoke", None))


def test_make_supervisor_with_prompt(fake_llm: ToolCapableFakeLLM) -> None:
    worker = factory_mod.make_agent(name="worker2", llm=fake_llm)
    supervisor = mod.make_supervisor(
        agents=[worker],
        llm=fake_llm,
        prompt="Coordinate all workers.",
    )
    assert callable(getattr(supervisor, "invoke", None))


def test_make_supervisor_custom_name(fake_llm: ToolCapableFakeLLM) -> None:
    worker = factory_mod.make_agent(name="worker3", llm=fake_llm)
    supervisor = mod.make_supervisor(
        agents=[worker],
        llm=fake_llm,
        supervisor_name="orchestrator",
    )
    assert callable(getattr(supervisor, "invoke", None))
