from utils.tools_registry import register_tool
from core.namespace_manager import list_namespaces, namespace_detail, create_namespace, delete_namespace
from llm_tools.k8s_tools.config import config_file
from typing import Dict, Any, Optional


@register_tool(
    name="get_namespace_list",
    description="获取当前 Kubernetes 集群中的所有命名空间",
    parameters={"type": "object", "properties": {}, "required": []}
)
def get_namespace_list_tool() -> Dict[str, Any]:
    """
    Retrieves a list of all namespaces in the current Kubernetes cluster.

    Returns:
        Dict[str, Any]: A dictionary containing the list of namespaces.

    Example:
        >>> get_namespace_list_tool()
        {'namespaces': ['default', 'kube-system', 'dev']}
    """
    result = list_namespaces(config_path=config_file)
    return result


@register_tool(
    name="get_namespace_detail",
    description="获取指定 Kubernetes 命名空间的详细信息",
    parameters={
        "type": "object",
        "properties": {
            "namespace_name": {"type": "string", "description": "命名空间名称"}
        },
        "required": ["namespace_name"]
    }
)
def get_namespace_detail_tool(namespace_name: str) -> Dict[str, Any]:
    """
    Retrieves detailed information about a specific Kubernetes namespace.

    Args:
        namespace_name (str): The name of the namespace to query.

    Returns:
        Dict[str, Any]: A dictionary containing details of the specified namespace.

    Example:
        >>> get_namespace_detail_tool("dev")
        {'name': 'dev', 'labels': {'env': 'development'}, 'status': 'Active'}
    """
    result = namespace_detail(ns_name=namespace_name, config_path=config_file)
    return result



@register_tool(
    name="create_namespace",
    description="创建 Kubernetes 命名空间",
    parameters={
        "type": "object",
        "properties": {
            "namespace_name": {"type": "string", "description": "命名空间名称"},
            "label_name": {"type": "string", "description": "命名空间 label，格式为 key=value"}
        },
        "required": ["namespace_name"]
    }
)
def create_namespace_tool(namespace_name: str, label_name: Optional[str] = None) -> Dict[str, Any]:
    """
    Creates a new Kubernetes namespace with an optional label.

    Args:
        namespace_name (str): The name of the new namespace.
        label_name (Optional[str]): An optional label in key=value format.

    Returns:
        Dict[str, Any]: A dictionary indicating the creation result.

    Example:
        >>> create_namespace_tool("test", "env=testing")
        {'message': 'Namespace created successfully', 'name': 'test'}
    """
    result = create_namespace(ns_name=namespace_name, label=label_name, config_path=config_file)
    return result


@register_tool(
    name="delete_namespace",
    description="删除 Kubernetes 命名空间",
    parameters={
        "type": "object",
        "properties": {
            "namespace_name": {"type": "string", "description": "命名空间名称"}
        },
        "required": ["namespace_name"]
    }
)
def delete_namespace_tool(namespace_name: str) -> Dict[str, Any]:
    """
    Deletes a specific Kubernetes namespace.

    Args:
        namespace_name (str): The name of the namespace to delete.

    Returns:
        Dict[str, Any]: A dictionary indicating the deletion result.

    Example:
        >>> delete_namespace_tool("dev")
        {'message': 'Namespace deleted successfully', 'name': 'dev'}
    """
    result = delete_namespace(ns_name=namespace_name, config_path=config_file)
    return result
