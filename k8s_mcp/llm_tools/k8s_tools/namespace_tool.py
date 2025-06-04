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
    result = delete_namespace(ns_name=namespace_name, config_path=config_file)
    return result
