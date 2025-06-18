from utils.tools_registry import register_tool
from core.node_manager import node_list
from llm_tools.k8s_tools.config import config_file

@register_tool(
    name="get_node_list",
    description="获取 Kubernetes 节点列表",
    parameters={"type": "object", "properties": {}, "required": []}
)
def get_node_list_tool():
    """
    Retrieves the list of nodes in the current Kubernetes cluster.

    Returns:
        Dict[str, Any]: A dictionary containing information about all nodes.

    Example:
        >>> get_node_list_tool()
        {
            "nodes": [
                {"name": "node-1", "status": "Ready"},
                {"name": "node-2", "status": "NotReady"}
            ]
        }
    """
    result = node_list(config_path=config_file)
    return result

