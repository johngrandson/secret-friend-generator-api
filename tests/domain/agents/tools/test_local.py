import pytest

import src.domain.agents.tools.local as mod


@pytest.mark.asyncio
async def test_add_integers() -> None:
    result = await mod.add.ainvoke({"a": 3, "b": 7})
    assert result == "10.0"


@pytest.mark.asyncio
async def test_add_floats() -> None:
    result = await mod.add.ainvoke({"a": 1.5, "b": 2.5})
    assert result == "4.0"


@pytest.mark.asyncio
async def test_add_negative() -> None:
    result = await mod.add.ainvoke({"a": -4, "b": 4})
    assert result == "0.0"


@pytest.mark.asyncio
async def test_multiply_basic() -> None:
    result = await mod.multiply.ainvoke({"a": 3, "b": 7})
    assert result == "21.0"


@pytest.mark.asyncio
async def test_multiply_by_zero() -> None:
    result = await mod.multiply.ainvoke({"a": 99, "b": 0})
    assert result == "0.0"


@pytest.mark.asyncio
async def test_multiply_floats() -> None:
    result = await mod.multiply.ainvoke({"a": 2.5, "b": 4.0})
    assert result == "10.0"


@pytest.mark.asyncio
async def test_echo_returns_same_text() -> None:
    result = await mod.echo.ainvoke({"text": "hello world"})
    assert result == "hello world"


@pytest.mark.asyncio
async def test_echo_empty_string() -> None:
    result = await mod.echo.ainvoke({"text": ""})
    assert result == ""


@pytest.mark.asyncio
async def test_echo_preserves_whitespace() -> None:
    result = await mod.echo.ainvoke({"text": "  spaces  "})
    assert result == "  spaces  "
