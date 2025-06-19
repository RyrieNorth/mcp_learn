import sys

from mcp.server.fastmcp import FastMCP

from typing import List, Dict, Any, Optional, Tuple, Union, Literal

from utils.logger import logger, set_log_file, set_log_level
from utils.kubernetes_manager import KubernetesManager

set_log_file("server.log")

# Create Kubernetes MCP Server
host = "0.0.0.0"
port = 8000
mcp = FastMCP("Kubernetes Resources Manager Server", host=host, port=port, log_level="INFO", log_requests=True)
logger.info(f"MCP '{mcp.name}' initialized on {host}:{port}")

# Create Kubernetes Resources Manager object
km = KubernetesManager()

# Register mcp tools
@mcp.tool()
def get_resources(
    resource_type: str,
    name: Optional[str] = None,
    namespace: Optional[str] = None,
    output_type: Optional[str] = "json"
) -> List[Dict[str, Any]]:
    """
    通用资源获取函数

    Args:
        resource_type (str): 资源类型，如 'nodes'、'namespaces'、'pods'、'services'、'deployments'
        name (Optional[str]): 资源名称（如pod名、node名等）
        namespace (Optional[str]): 命名空间（如适用）
        output_type (Optional[str]): 输出类型

    Returns:
        List[Dict[str, Any]]: 资源信息
    """
    if resource_type == "nodes":
        return km.get.get_nodes(node_name=name, output_type=output_type)
    elif resource_type == "namespaces":
        return km.get.get_namespaces(namespace=name, output_type=output_type)
    elif resource_type == "pods":
        return km.get.get_pods(pod_name=name, namespace=namespace, output_type=output_type)
    elif resource_type == "services":
        return km.get.get_services(service=name, namespace=namespace, output_type=output_type)
    elif resource_type == "deployments":
        return km.get.get_deployment_apps(app_name=name, namespace=namespace, output_type=output_type)
    else:
        raise ValueError(f"不支持的资源类型: {resource_type}")


tool_count = 0
for tool in mcp._tool_manager.list_tools():
    logger.info(f"Registered tool: {tool.name}")
    tool_count +=1

logger.info(f"Total registered tools: {tool_count}")


if __name__ == "__main__":
    try:
        mcp.run(transport="streamable-http")
    except KeyboardInterrupt:
        logger.info(f"Closing Libvirt Server...")
        sys.exit(0)
    except EOFError:
        logger.info(f"Closing Libvirt Server...")
        sys.exit(0)