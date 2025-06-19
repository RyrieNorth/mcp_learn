import os

def is_debug_mode() -> bool:
    """启动debug模式"""
    return os.environ.get("DEBUG", "false").strip().lower() == "true"
