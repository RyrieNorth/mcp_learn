import sys
import socket
import netifaces

from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Any, Optional, Literal

from utils.functions import parse_labels
from utils.logger import logger, set_log_file, set_log_level
from utils.kubernetes_manager import KubernetesManager



set_log_level("DEBUG")
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
    all_namespace: Optional[bool] = False,
    output_type: Optional[str] = "json"
) -> List[Dict[str, Any]]:
    """
    通用资源获取函数

    Args:
        resource_type (str): 资源类型，如 'nodes'、'namespaces'、'pods'、'services'、'deployments'
        name (Optional[str]): 资源名称（如pod名、node名等）
        namespace (Optional[str]): 命名空间（如适用）
        all_namespace (Optional[bool]): 当设定为True时，则列出所有命名空间下对应的资源，反之仅列出'default'命名空间下的资源
        output_type (Optional[str]): 输出类型，默认为json，支持yaml、wide，当非详细查询时，建议使用wide列出少量结果

    Returns:
        List[Dict[str, Any]]: 资源信息
    """
    try:
        if resource_type == "nodes":
            return km.get.get_nodes(
                node_name=name,
                output_type=output_type
            )
            
        elif resource_type == "namespaces":
            return km.get.get_namespaces(
                namespace=name,
                output_type=output_type
            )
            
        elif resource_type == "pods":
            return km.get.get_pods(
                pod_name=name,
                namespace=namespace,
                all_namespace=all_namespace,
                output_type=output_type
            )
            
        elif resource_type == "services":
            return km.get.get_services(
                service=name,
                namespace=namespace,
                all_namespace=all_namespace,
                output_type=output_type
            )
            
        elif resource_type == "deployments":
            return km.get.get_deployment_apps(
                app_name=name,
                namespace=namespace,
                all_namespace=all_namespace,
                output_type=output_type
            )
            
        else:
            raise ValueError(f"Unsupport resource type: {resource_type}")
        
    except Exception as e:
        logger.error(f"[get_resources] Error: {str(e)}")
        return f"[get_resources] Failed: {str(e)}"

@mcp.tool()
def delete_resources(
    resource_type: str,
    name: Optional[str] = None,
    namespace: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    通用资源删除函数

    Args:
        resource_type (str): 资源类型，如 'nodes'、'namespaces'、'pods'、'services'、'deployments'
        name (Optional[str]): 资源名称（如pod名、node名等）
        namespace (Optional[str]): 命名空间（如适用）

    Returns:
        List[Dict[str, Any]]: 删除信息
    """
    try:
        if resource_type == "namespaces":
            return km.delete.delete_namespaces(namespaces=name)
        
        elif resource_type == "pods":
            return km.delete.delete_pods(pod_name=name, namespace=namespace)
        
        elif resource_type == "services":
            return km.delete.delete_services(services=name, namespace=namespace)
        
        elif resource_type == "deployments":
            return km.delete.delete_deployment_apps(app_name=name, namespace=namespace)
        
        else:
            raise ValueError(f"Unsupport resource type: {resource_type}")
        
    except Exception as e:
        logger.error(f"[delete_resources] Error: {str(e)}")
        return f"[delete_resources] Failed: {str(e)}"

@mcp.tool()
def describe_resources(
    resource_type: str,
    name: Optional[str] = None,
    namespace: Optional[str] = None,
    all_namespace: Optional[bool] = False,
) -> List[Dict[str, Any]]:
    """
    通用资源描述函数

    Args:
        resource_type (str): 资源类型，如 'nodes'、'namespaces'、'pods'、'services'、'deployments'
        name (Optional[str]): 资源名称（如pod名、node名等）
        namespace (Optional[str]): 命名空间（如适用）
        all_namespace (Optional[bool]): 当设定为True时，则列出所有命名空间下对应的资源，反之仅列出'default'命名空间下的资源

    Returns:
        List[Dict[str, Any]]: 资源信息
    """
    try:
        if resource_type == "nodes":
            return km.describe.describe_nodes(
                node_name=name,
            )
            
        elif resource_type == "namespaces":
            return km.describe.describe_namespaces(
                namespace=name,
            )
            
        elif resource_type == "pods":
            return km.describe.describe_pods(
                pod_name=name,
                namespace=namespace,
                all_namespace=all_namespace,
            )
            
        elif resource_type == "services":
            return km.describe.describe_services(
                service=name,
                namespace=namespace,
                all_namespace=all_namespace,
            )
            
        elif resource_type == "deployments":
            return km.describe.describe_deployments(
                app_name=name,
                namespace=namespace,
                all_namespace=all_namespace,
            )
            
        else:
            raise ValueError(f"Unsupport resource type: {resource_type}")
    except Exception as e:
        logger.error(f"[describe_resources] Error: {str(e)}")
        return f"[describe_resources] Failed: {str(e)}"

@mcp.tool()
def get_api_resources(
    api_group: Optional[str] = None,
    namespaced: Optional[bool] = None,
    output_type: Optional[str] = 'wide',
) -> Dict:
    """获取kubernetes可用api资源类型

    Args:
        api_group (Optional[str], optional): api资源类型
        namespaced (Optional[bool], optional): 是否支持namespace
        output_type (Optional[str], optional): 输出类型，支持wide

    Raises:
        RuntimeError: 当subprocess执行错误时抛出异常

    Returns:
        Dict: api资源类型
    """
    try:
        return km.list.kubectl_get_api_resoucrs(
            api_group=api_group,
            namespaced=namespaced,
            output_type=output_type
        )
    except Exception as e:
        logger.error(f"[get_api_resources] Error: {str(e)}")
        return f"[get_api_resources] Failed: {str(e)}"

@mcp.tool()
def get_resources_logs(
    resource_type: str,
    resource_name: str,
    namespace: str = 'default',
    container: Optional[str] = None,
    tail: Optional[str] = None,
    since: Optional[str] = None,
    since_time: Optional[str] = None,
    timestamps: bool = False,
    previous: bool = False,
    label_selector: Optional[str] = None,
) -> str:
    """
    获取指定 Kubernetes 资源的日志。

    Args:
        resource_type (str): 支持 pod, deployment, job, cronjob。
        resource_name (str): 资源名称。
        namespace (str, optional): 命名空间，默认为 default。
        container (str, optional): 容器名称。
        tail (str, optional): 最后 N 行日志。
        since (str, optional): 获取 N 时间前的日志（如 5s、1m）。
        since_time (str, optional): RFC3339 格式的时间起点。
        timestamps (bool, optional): 是否显示时间戳。
        previous (bool, optional): 是否包含之前的容器日志。
        label_selector (str, optional): 用于匹配 Pod 的自定义 label。
        kubeconfig_path (str, optional): kubeconfig 路径，默认 /root/.kube/config。

    Returns:
        str: 日志字符串。
    """
    try:
        return km.logs.kubectl_logs(
            resource_type=resource_type,
            resource_name=resource_name,
            namespace=namespace,
            container=container,
            tail=tail,
            since=since,
            sinceTime=since_time,
            timestamps=timestamps,
            previous=previous,
            labelSelector=label_selector
        )
    except Exception as e:
        logger.error(f"[get_resources_logs] Error: {str(e)}")
        return f"Error retrieving logs: {str(e)}"

@mcp.tool()
def patch_resource(
    resource_type: str,
    resource_name: str,
    patch: Dict,
    namespace: str = "default",
    patch_type: str = "strategic",
) -> str:
    """
    给指定 Kubernetes 资源打补丁（patch）。

    Args:
        resource_type (str): 资源类型，如 deployment。
        resource_name (str): 资源名称。
        patch (Dict): 要应用的 patch 内容（字典格式）。
        namespace (str): 命名空间。
        patch_type (str): patch 类型，默认 strategic。
        kubeconfig_path (str): kubeconfig 路径。

    Returns:
        str: 执行结果。
    """
    try:
        return km.patch.kubectl_patch(
            resource_type=resource_type,
            resource_name=resource_name,
            patch=patch,
            namespace=namespace,
            patch_type=patch_type
        )
    except Exception as e:
        logger.error(f"[patch_resource] Error: {str(e)}")
        return f"[patch_resource] Failed: {str(e)}"

@mcp.tool()
def port_forward(
    action: Literal['start', 'stop'],
    resource_type: Optional[str] = None,
    resource_name: Optional[str] = None,
    local_port: Optional[int] = None,
    remote_port: Optional[int] = None,
    proc_id: Optional[int] = None,
    namespace: str = 'default'
) -> str:
    """
    启动或停止本地端口映射到 Kubernetes 资源。

    Args:
        resource_type (str): 资源类型，如 pod、deployment
        resource_name (str): 资源名称
        local_port (int): 本地端口
        remote_port (int): 容器中暴露的远程端口
        namespace (str, optional): 命名空间，默认 default
        action (str, optional): 操作类型，start 启动，stop 停止
        proc_id (int, optional): 若 action 为 stop，需要传入要终止的进程 ID

    Returns:
        str: 执行结果或错误信息
    """
    try:
        if action == "start":
            if not resource_type or not resource_name or local_port is None or remote_port is None:
                raise ValueError("When action is 'start', resource_type, resource_name, local_port and remote_port are required.")

            ip_list = [
                addr['addr']
                for iface in netifaces.interfaces()
                for addr in netifaces.ifaddresses(iface).get(netifaces.AF_INET, [])
                if not addr['addr'].startswith(("127.", "172.", "169.254.")) and addr['addr'] != "0.0.0.0"
            ]
                     
            return km.portforward.start_port_forward(
                resource_type=resource_type,
                resource_name=resource_name,
                local_port=local_port,
                remote_port=remote_port,
                namespace=namespace,
            ), f"Now port-forwarding {ip_list}:{local_port} to {resource_name}"
            
        elif action == "stop":
            if proc_id is None:
                raise ValueError("When action is 'stop', proc_id is required.")
            return km.portforward.stop_port_forward(proc_id=proc_id)
        else:
            raise ValueError(f"Unsupported action: {action}")
        
    except Exception as e:
        logger.error(f"[port_forward] Error: {str(e)}")
        return f"[port_forward] Failed: {str(e)}"

@mcp.tool()
def create_resource(
    resource_type: Optional[str],
    resource_name: Optional[str],
    pod_image: Optional[str] = None,
    pod_ports: Optional[List[int]] = None,
    pod_image_pull_policy: str = 'IfNotPresent',
    deployment_replicas: Optional[int] = 1,
    configmap_data: Optional[List[Dict[str, Any]]] = None,
    secret_type: Optional[str] = None,
    secret_data: Optional[List[Dict[str, Any]]] = None,
    secret_cert: Optional[str] = None,
    secret_key: Optional[str] = None,
    secret_docker_username: Optional[str] = None,
    secret_docker_password: Optional[str] = None,
    secret_docker_server: Optional[str] = None,
    service_protocol: Optional[str] = 'TCP',
    service_port_name: Optional[str] = None,
    service_targetPort: Optional[int] = None,
    service_nodePort: Optional[int] = None,
    service_selector: Optional[Dict[str, str]] = None,
    service_type: str = "ClusterIP",
    service_ports: Optional[List[Dict[str, Any]]] = None,
    namespace: Optional[str] = 'default',
    labels: Optional[Dict[str, str]] = None,
) -> str:
    """创建 Kubernetes 资源。

    支持的资源类型包括：
    - namespaces
    - pods
    - deployments
    - configmap
    - serviceAccount
    - secret（generic、tls、docker-registry 类型）
    - services

    Args:
        resource_type (Optional[str]): 资源类型，例如 'pods'、'deployments' 等。
        resource_name (Optional[str]): 要创建的资源名称。
        pod_image (Optional[str], optional): Pod 或 Deployment 使用的容器镜像。
        pod_ports (Optional[List[int]], optional): 容器暴露的端口列表。
        pod_image_pull_policy (str, optional): 镜像拉取策略，默认值为 'IfNotPresent'。
        deployment_replicas (Optional[int], optional): Deployment 副本数量，默认为 1。
        configmap_data (Optional[List[Dict[str, Any]]], optional): ConfigMap 数据，格式为键值对字典的列表。
        secret_type (Optional[str], optional): Secret 类型，支持 'generic'、'tls' 和 'docker-registry'。
        secret_data (Optional[List[Dict[str, Any]]], optional): Secret 数据，适用于 generic 类型，格式为字典列表。
        secret_cert (Optional[str], optional): TLS 类型 Secret 的证书路径。
        secret_key (Optional[str], optional): TLS 类型 Secret 的私钥路径。
        secret_docker_username (Optional[str], optional): Docker Registry 类型的用户名。
        secret_docker_password (Optional[str], optional): Docker Registry 类型的密码。
        secret_docker_server (Optional[str], optional): Docker Registry 的服务地址（如 https://registry.example.com）。
        service_protocol (Optional[str], optional): Service 协议类型，支持 'TCP' 或 'UDP'，默认为 'TCP'。不支持小写！
        service_port_name (Optional[str], optional): Service 端口的命名，当有多个端口对象时需要指定。
        service_targetPort (Optional[int], optional): 后端 Pod 暴露的目标端口。
        service_nodePort (Optional[int], optional): NodePort 类型 Service 对外暴漏的固定端口，当类型设定为NodePort时要指定。
        service_selector (Optional[Dict[str, str]], optional): 用于匹配后端 Pod 的 label。
        service_type (str, optional): Service 类型，支持 'ClusterIP'、'NodePort'，默认为 'ClusterIP'。
        service_ports (Optional[List[Dict[str, Any]]], optional): 多端口定义的完整字典列表，优先于单个端口配置。
        namespace (Optional[str], optional): 所属命名空间，默认为 'default'。
        labels (Optional[str], optional): 附加标签（label），字符串格式（JSON 字符串），如 '{"app": "nginx"}'。

    Returns:
        str: 资源创建结果或错误信息。
    """

    try:
        labels_dict = parse_labels(labels)

        if resource_type == "namespaces":
            return km.create.create_namespace(
                ns_name=resource_name,
                labels=labels_dict
            )

        elif resource_type == "pods":
            containers = [
                km.create.build_container(
                    name=resource_name,
                    image=pod_image,
                    ports=pod_ports,
                    image_pull_policy=pod_image_pull_policy
                )
            ]
            return km.create.create_pod(
                pod_name=resource_name,
                labels=labels_dict,
                containers=containers,
                namespace=namespace
            )

        elif resource_type == "deployments":
            containers = [
                km.create.build_container(
                    name=resource_name,
                    image=pod_image,
                    ports=pod_ports,
                    image_pull_policy=pod_image_pull_policy
                )
            ]
            return km.create.create_deployment(
                name=resource_name,
                replicas=deployment_replicas,
                labels=labels_dict,
                containers=containers,
                namespace=namespace
            )

        elif resource_type == "configmap":
            return km.create.create_configmap(
                map_name=resource_name,
                data=configmap_data,
                namespace=namespace
            )

        elif resource_type == "serviceAccount":
            return km.create.create_serviceAccount(
                sa_name=resource_name,
                labels=labels_dict,
                namespace=namespace
            )

        elif resource_type == "secret":
            return km.create.create_secret(
                secret_type=secret_type,
                name=resource_name,
                namespace=namespace,
                data=secret_data,
                cert=secret_cert,
                key=secret_key,
                docker_username=secret_docker_username,
                docker_password=secret_docker_password,
                docker_server=secret_docker_server
            )

        elif resource_type == "services":
            ports = service_ports or [
                km.create.build_port(
                    name=service_port_name,
                    protocol=service_protocol,
                    port=service_targetPort,
                    targetPort=service_targetPort,
                    nodePort=service_nodePort
                )
            ]
            return km.create.create_service(
                service_name=resource_name,
                labels=labels_dict,
                ports=ports,
                selector=service_selector,
                service_type=service_type,
                namespace=namespace
            )

        else:
            raise ValueError(f"Unsupport resource type: {resource_type}")

    except Exception as e:
        logger.error(f"[create_resource] Error: {str(e)}")
        return f"Error creating resource: {str(e)}"
    

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