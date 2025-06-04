tool_registry = {}

def register_tool(name: str, description: str, parameters: dict):
    def decorator(func):
        tool_registry[name] = {
            "function": func,
            "openai_tool": {
                "type": "function",
                "function": {
                    "name": name,
                    "description": description,
                    "parameters": parameters,
                },
            },
        }
        return func
    return decorator
