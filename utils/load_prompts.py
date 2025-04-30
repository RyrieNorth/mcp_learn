import yaml
from .logger import logger
from typing import Optional, Dict


def load_prompts() -> Optional[Dict]:
    """
    加载本地 prompts 配置文件 prompts.yaml

    Returns:
        dict | None: 成功时返回提示字典，失败时返回 None
    """
    try:
        with open("prompts.yaml", "r", encoding="utf-8") as file:
            return yaml.safe_load(file)
    except FileNotFoundError as err:
        logger.error(f"读取prompts文件失败: {err}")
        return None
