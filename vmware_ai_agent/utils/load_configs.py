import yaml
from .logger import logger
from typing import Optional, Dict


def load_configs() -> Optional[Dict]:
    """
    加载本地配置文件 config.yaml

    Returns:
        dict | None: 成功时返回配置字典，失败时返回 None
    """
    try:
        with open("config.yaml", "r", encoding="utf-8") as file:
            return yaml.safe_load(file)
    except FileNotFoundError as err:
        logger.error(f"读取配置文件失败: {err}")
        return None
