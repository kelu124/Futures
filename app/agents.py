from langchain_core.tools import tool

# See https://python.langchain.com/docs/how_to/tools_chain/



@tool
def multiply(first_int: int, second_int: int) -> int:
    """Multiply two integers together."""
    return first_int * second_int

