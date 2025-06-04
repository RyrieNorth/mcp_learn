from utils.tools_registry import tool_registry
from utils.logger import logger

def get_openai_tool_specs():
    """
    Retrieves the list of OpenAI-compatible tool schemas from the tool registry.

    Returns:
        List[Dict]: A list of tool specifications formatted for OpenAI's tool calling interface.
    """
    return [item["openai_tool"] for item in tool_registry.values()]


def call_tool_by_name(name, arguments: dict):
    """
    Dynamically calls a registered tool by its name using the provided arguments.

    Args:
        name (str): The name of the tool to call.
        arguments (dict): The arguments to pass to the tool's function.

    Returns:
        Any: The result returned by the tool function.

    Raises:
        ValueError: If the tool is not found in the registry.
    """
    logger.info(f"Calling tool {name} with arguments: {arguments}")
    tool = tool_registry.get(name)
    if not tool:
        raise ValueError(f"Tool {name} not registry")
    return tool["function"](**arguments)
