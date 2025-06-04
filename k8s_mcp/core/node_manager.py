from typing import List, Optional
from core.client_manager import get_core_v1_api


def node_list(config_path: Optional[str] = None) -> List[str]:
    api = get_core_v1_api(config_path=config_path)
    return [node.metadata.name for node in api.list_node().items]

