from langchain_core.tools import tool


@tool
async def add(a: float, b: float) -> str:
    """Add two numbers together.

    Args:
        a: First operand.
        b: Second operand.

    Returns:
        String representation of the sum.
    """
    return str(a + b)


@tool
async def multiply(a: float, b: float) -> str:
    """Multiply two numbers together.

    Args:
        a: First operand.
        b: Second operand.

    Returns:
        String representation of the product.
    """
    return str(a * b)


@tool
async def echo(text: str) -> str:
    """Echo text back unchanged.

    Args:
        text: Input text to echo.

    Returns:
        The same text that was passed in.
    """
    return text
