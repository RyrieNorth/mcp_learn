import os

def is_debug_mode() -> bool:
    """
    Determine whether the application is running in debug mode.

    Returns:
        bool: True if the 'DEBUG' environment variable is set to 'true' (case-insensitive), False otherwise.
    """
    return os.environ.get("DEBUG", "false").strip().lower() == "true"
