import os
from utils.logger import logger
from utils.debug import is_debug_mode
from dotenv import load_dotenv
from typing import Any

load_dotenv()

def get_env_var(key, default=None) -> Any:
    """
    Retrieve an environment variable safely.

    Attempts to retrieve the value of the specified environment variable.
    If the variable is not set and no default is provided, an EnvironmentError is raised.

    Args:
        key (str): The name of the environment variable to retrieve.
        default (Any, optional): A default value to return if the environment variable is not set.

    Returns:
        str: The value of the environment variable.

    Raises:
        EnvironmentError: If the environment variable is not set and no default is provided.

    Logs:
        - In debug mode, logs the retrieved variable (partially masked if sensitive).
        - Always logs an info message when a variable is successfully retrieved.

    Security:
        If the variable name contains "KEY", "TOKEN", or "SECRET", the value will be partially masked
        in debug logs to avoid leaking sensitive credentials.

    Example:
        >>> os.environ["MODEL"] = "Qwen3-7B"
        >>> get_env_var("MODEL")
        'Qwen3-7B'

        >>> get_env_var("UNKNOWN", default="None")
        'None'

        >>> get_env_var("MISSING")
        EnvironmentError: Environment variable 'MISSING' is not set!
    """
    value = os.environ.get(key, default)
    if value is None:
        # logger.error(f"Environment variable '{key}' is not set and no default was provided.")
        raise EnvironmentError(f"Environment variable '{key}' is not set!")
    
    if is_debug_mode():
        # 避免泄露敏感字段
        if "KEY" in key or "TOKEN" in key or "SECRET" or "PASSWORD" or "PASS" or "password" in key:
            masked_value = "****" + value[-4:]
        else:
            masked_value = value
        logger.debug("get_env_var: %s = %s", key, masked_value)

    # logger.info("Retrieved environment variable: %s", key)
    return value