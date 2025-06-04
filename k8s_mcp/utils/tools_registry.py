# Global tool registry where all tools are stored
tool_registry = {}

def register_tool(name: str, description: str, parameters: dict):
    """
    A decorator used to register a Python function as an OpenAI-compatible tool.

    Args:
        name (str): The name of the tool. This should match the function name expected by OpenAI's function calling.
        description (str): A human-readable description of what the tool does.
        parameters (dict): A JSON Schema describing the tool's input parameters (types, required fields, etc.).

    Returns:
        Callable: A decorator that registers the function and returns it unmodified.
    
    Example:
        >>> 
            @register_tool(
            name="get_weather",
            description="Get the current weather in a given city.",
            parameters={
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "units": {"type": "string", "enum": ["metric", "imperial"]}
                },
                "required": ["city"]
            }
            )
            def get_weather(city: str, units: str = "metric") -> str:
                # Simulate fetching weather
                return f"The weather in {city} is 25°C with units in {units}."

    """
    def decorator(func):
        # Register the function and its OpenAI tool schema in the global tool registry
        tool_registry[name] = {
            "function": func,
            "openai_tool": {
                "type": "function",  # Specifies OpenAI tool calling type
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters,
                },
            },
        }
        return func  # Return the original function
    return decorator
