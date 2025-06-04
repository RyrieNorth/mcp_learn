from utils.tools_registry import register_tool
from core.service_manager import *
from llm_tools.k8s_tools.config import config_file
from typing import Dict, Any, List, Optional


@register_tool(
    name="get_service_list",
    description="获取 Kubernetes 集群中所有服务",
    parameters={"type": "object", "properties": {}, "required": []}
)
def get_service_list_tool() -> Dict[str, Any]:
    """
    Retrieve the list of all Services in the Kubernetes cluster.

    Returns:
        Dict[str, Any]: A dictionary containing the list of all Services.

    Example:
        services = get_service_list_tool()
        print(services)
    """
    result = service_list(config_path=config_file)
    return result


def get_service_detail_tool(service_name: str, namespace_name: str = None) -> Dict[str, Any]:
    """
    Retrieve detailed information about a specific Kubernetes Service.

    Args:
        service_name (str): The name of the Service to retrieve.
        namespace_name (str, optional): Namespace where the Service resides. Defaults to None (default namespace).

    Returns:
        Dict[str, Any]: A dictionary containing detailed information of the specified Service.

    Example:
        >>> 
        detail = get_service_detail_tool(service_name="my-service", namespace_name="default")
        print(detail)
    """
    result = service_detail(service_name=service_name, namespace_name=namespace_name, config_path=config_file)
    return result


@register_tool(
    name="create_service",
    description="创建 Kubernetes Service，支持多端口与 Selector",
    parameters={
        "type": "object",
        "properties": {
            "service_name": {"type": "string", "description": "Service 名称"},
            "namespace_name": {"type": "string", "description": "命名空间"},
            "selector": {
                "type": "object",
                "description": "Pod selector，例如 {\"app\": \"my-app\"}",
                "additionalProperties": {"type": "string"}
            },
            "service_type": {
                "type": "string",
                "enum": ["ClusterIP", "NodePort", "LoadBalancer"],
                "description": "Service 类型"
            },
            "ports": {
                "type": "array",
                "description": "端口列表，支持多个端口",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "port": {"type": "integer"},
                        "targetPort": {"type": "integer"},
                        "nodePort": {"type": "integer"},
                        "protocol": {"type": "string", "enum": ["TCP", "UDP"]}
                    },
                    "required": ["name", "port"]
                }
            }
        },
        "required": ["service_name", "namespace_name", "ports", "service_type"]
    }
)
def create_service_tool(
    service_name: str,
    namespace_name: str,
    ports: List[Dict],
    selector: Optional[Dict[str, str]] = None,
    service_type: Optional[str] = "ClusterIP",
    config_path=config_file
) -> Dict[str, Any]:
    """
    Create a Kubernetes Service.

    Args:
        service_name (str): Name of the Service.
        namespace_name (str): Namespace in which to create the Service.
        ports (List[Dict]): List of port configurations, each containing name, port number, targetPort, etc.
        selector (Optional[Dict[str, str]]): Pod selector labels to match the Service to Pods.
        service_type (Optional[str]): Type of the Service; one of "ClusterIP", "NodePort", or "LoadBalancer". Defaults to "ClusterIP".
        config_path: Path to the kubeconfig file, defaults to the global config.

    Returns:
        Dict[str, Any]: Response information after creating the Service.

    Example:
        ports = [
            {"name": "http", "port": 80, "targetPort": 8080, "protocol": "TCP"},
            {"name": "https", "port": 443, "targetPort": 8443, "protocol": "TCP"}
        ]
        selector = {"app": "my-app"}
        response = create_service_tool(
            service_name="my-service",
            namespace_name="default",
            ports=ports,
            selector=selector,
            service_type="ClusterIP"
        )
        print(response)
    """
    result = create_service(
        service_name=service_name,
        namespace_name=namespace_name,
        ports=ports,
        selector=selector,
        service_type=service_type,
        config_path=config_path
    )
    return result


@register_tool(
    name="delete_service",
    description="删除 Kubernetes service",
    parameters={
        "type": "object",
        "properties": {
            "service_name": {"type": "string", "description": "Service 名称"},
            "namespace_name": {"type": "string", "description": "命名空间名称"},
        },
        "required": ["service_name", "namespace_name"]
    }
)
def delete_service_tool(service_name: str, namespace_name: str) -> Dict[str, Any]:
    """
    Delete a specified Kubernetes Service.

    Args:
        service_name (str): Name of the Service to delete.
        namespace_name (str): Namespace where the Service is located.

    Returns:
        Dict[str, Any]: Result information of the delete operation.

    Example:
        result = delete_service_tool(service_name="my-service", namespace_name="default")
        print(result)
    """
    result = delete_service(service_name=service_name, namespace_name=namespace_name, config_path=config_file)
    return result