from utils.tools_registry import register_tool
from core.pod_manager import *
from llm_tools.k8s_tools.config import config_file
from typing import Dict, Any


@register_tool(
    name="get_pod_list",
    description="获取 Kubernetes 集群中所有 Pod",
    parameters={"type": "object", "properties": {}, "required": []}
)
def get_pod_list_tool():
    """
    Retrieves a list of all Pods in the current Kubernetes cluster.

    Returns:
        Dict[str, Any]: A dictionary containing the list of all pods.

    Example:
        >>> get_pod_list_tool()
        {
            "pods": [
                {"name": "nginx-pod", "namespace": "default"},
                {"name": "redis-pod", "namespace": "dev"}
            ]
        }
    """
    result = pod_list(config_path=config_file)
    return result


@register_tool(
    name="get_pod_detail",
    description="获取指定 Pod 的详细信息",
    parameters={
        "type": "object",
        "properties": {
            "pod_name": {"type": "string", "description": "Pod 名称"}
        },
        "required": ["pod_name"]
    }
)
def get_pod_detail_tool(pod_name: str, namespace_name: str = None) -> Dict[str, Any]:
    """
    Retrieves detailed information of a specified Pod.

    Args:
        pod_name (str): The name of the Pod.
        namespace_name (str, optional): The namespace of the Pod. Defaults to None.

    Returns:
        Dict[str, Any]: Detailed information about the Pod.

    Example:
        >>> get_pod_detail_tool("nginx-pod", "default")
        {
            "name": "nginx-pod",
            "status": "Running",
            "containers": [...],
            ...
        }
    """
    result = pod_detail(pod_name=pod_name, namespace_name=namespace_name, config_path=config_file)
    return result


@register_tool(
    name="create_pod",
    description="创建 Kubernetes Pod，支持多 container、端口、volumeMounts、环境变量等",
    parameters={
        "type": "object",
        "properties": {
            "pod_name": {"type": "string", "description": "Pod 名称"},
            "namespace_name": {"type": "string", "description": "命名空间"},
            "labels": {
                "type": "object",
                "description": "Pod 标签，用于被 Service Selector 匹配，例如 {\"app\": \"my-app\"}",
                "additionalProperties": {"type": "string"}
            },
            "containers": {
                "type": "array",
                "description": "容器列表",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "image": {"type": "string"},
                        "ports": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "containerPort": {"type": "integer"},
                                    "protocol": {"type": "string", "enum": ["TCP", "UDP"]}
                                },
                                "required": ["containerPort"]
                            }
                        },
                        "imagePullPolicy": {
                            "type": "string",
                            "enum": ["Always", "IfNotPresent", "Never"],
                            "default": "IfNotPresent"
                        }
                    },
                    "required": ["name", "image"]
                }
            },
        },
        "required": ["pod_name", "namespace_name", "containers"]
    }
)
def create_pod_tool(
    pod_name: str,
    namespace_name: str,
    containers: List[Dict[str, Any]],
    volumes: Optional[List[Dict[str, Any]]] = None,
    labels: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Creates a Pod in the specified Kubernetes namespace.

    Args:
        pod_name (str): Name of the Pod.
        namespace_name (str): Target namespace for the Pod.
        containers (List[Dict[str, Any]]): List of containers with images, ports, etc.
        volumes (Optional[List[Dict[str, Any]]], optional): Volumes to mount in the Pod.
        labels (Optional[Dict[str, str]], optional): Labels to assign to the Pod.

    Returns:
        Dict[str, Any]: Result of the Pod creation process.

    Example:
        >>> create_pod_tool(
        ...     pod_name="my-pod",
        ...     namespace_name="default",
        ...     containers=[{"name": "nginx", "image": "nginx:latest"}],
        ...     labels={"app": "nginx"}
        ... )
        {
            "status": "Success",
            "message": "Pod created successfully"
        }
    """
    result = create_pod(
        pod_name=pod_name,
        namespace_name=namespace_name,
        container_names=containers,
        volumes=volumes,
        labels=labels,
        config_path=config_file
    )
    return result


@register_tool(
    name="delete_pod",
    description="删除 Kubernetes Pod",
    parameters={
        "type": "object",
        "properties": {
            "pod_name": {"type": "string", "description": "Pod 名称"},
            "namespace_name": {"type": "string", "description": "命名空间名称"},
        },
        "required": ["pod_name", "namespace_name"]
    }
)
def delete_service_tool(pod_name: str, namespace_name: str) -> Dict[str, Any]:
    """
    Deletes a specified Pod from a Kubernetes namespace.

    Args:
        pod_name (str): Name of the Pod to delete.
        namespace_name (str): Namespace where the Pod exists.

    Returns:
        Dict[str, Any]: Result of the deletion operation.

    Example:
        >>> delete_service_tool("nginx-pod", "default")
        {
            "status": "Success",
            "message": "Pod deleted successfully"
        }
    """
    result = delete_pod(pod_name=pod_name, namespace_name=namespace_name, config_path=config_file)
    return result
