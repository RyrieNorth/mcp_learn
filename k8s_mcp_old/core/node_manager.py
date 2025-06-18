from typing import List, Optional
from core.client_manager import get_core_v1_api


def node_list(config_path: Optional[str] = None) -> List[str]:
    """
    Retrieve the list of all node names in the Kubernetes cluster.

    Args:
        config_path (Optional[str]): Optional path to the kubeconfig file.

    Returns:
        List[str]: A list containing the names of all nodes in the cluster.
    """
    api = get_core_v1_api(config_path=config_path)
    return [node.metadata.name for node in api.list_node().items]
