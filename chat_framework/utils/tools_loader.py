from utils.tools_registry import tool_registry
from utils.logger import logger

def get_openai_tool_specs():
    return [item["openai_tool"] for item in tool_registry.values()]

def call_tool_by_name(name, arguments: dict):
    logger.info(f"Calling tool {name} with arguments: {arguments}")
    tool = tool_registry.get(name)
    if not tool:
        raise ValueError(f"Tool {name} not registry")
    return tool["function"](**arguments)