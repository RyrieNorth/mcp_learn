from utils.logger import logger
from typing import List, Optional, Dict, Any
from kubernetes import client
from core.client_manager import get_core_v1_api


def service_list(config_path: Optional[str] = None) -> List[str]:
    """
    Retrieve a list of all service names across all namespaces in the Kubernetes cluster.

    Args:
        config_path (Optional[str]): Path to the kubeconfig file. If None, default config is used.

    Returns:
        List[str]: A list of service names as strings.
    """
    api = get_core_v1_api(config_path=config_path)
    logger.info("Fetch all services...")
    return [svc.metadata.name for svc in api.list_service_for_all_namespaces().items]


def service_detail(service_name: str, namespace_name: str = None, config_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Retrieve detailed information about a specific service in the cluster.

    Args:
        service_name (str): The name of the service to query.
        namespace_name (Optional[str]): The namespace where the service resides. If None, searches all namespaces.
        config_path (Optional[str]): Path to the kubeconfig file.

    Returns:
        Optional[Dict[str, Any]]: A dictionary containing detailed service information such as:
            - service_name: Name of the service.
            - service_namespace: Namespace of the service.
            - service_type: Type of the service (e.g., ClusterIP, NodePort, LoadBalancer).
            - cluster_ip: Cluster internal IP address assigned to the service.
            - ports: List of ports exposed by the service, including port number, node port, protocol, and target port.
            - labels: Labels assigned to the service.
            - selector: Label selector used to target pods.
        Returns None if the service is not found.
    """
    api = get_core_v1_api(config_path)
    logger.info("Fetch service details...")
    for svc in api.list_service_for_all_namespaces().items:
        if svc.metadata.name == service_name and (namespace_name is None or svc.metadata.namespace == namespace_name):
            return {
                "service_name": svc.metadata.name,
                "service_namespace": svc.metadata.namespace,
                "service_type": svc.spec.type,
                "cluster_ip": svc.spec.cluster_ip,
                "ports": [
                    {
                        "name": ports.name,
                        "node_port": ports.node_port,
                        "port": ports.port,
                        "protocol": ports.protocol,
                        "target_port": ports.target_port,
                    } for ports in svc.spec.ports
                ],
                "labels": svc.metadata.labels or {},
                "selector": svc.spec.selector,
            }
    return None


def create_service(
    service_name: str,
    namespace_name: str,
    ports: List[Dict[str, Any]],
    selector: Optional[Dict[str, str]] = None,
    service_type: str = "ClusterIP",
    config_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new Kubernetes Service in a given namespace with specified parameters.

    Args:
        service_name (str): Name of the service to create.
        namespace_name (str): Namespace in which to create the service.
        ports (List[Dict[str, Any]]): List of port configurations. Each port dict may include:
            - name: Optional name of the port.
            - port: Port number exposed by the service.
            - targetPort: Port number on the target pods.
            - protocol: Protocol used (default is "TCP").
            - nodePort: (Optional) Node port number, required if service_type is "NodePort".
        selector (Optional[Dict[str, str]]): Label selector to identify target pods.
        service_type (str): Type of the service (e.g., "ClusterIP", "NodePort", "LoadBalancer").
        config_path (Optional[str]): Path to the kubeconfig file.

    Returns:
        Dict[str, Any]: Result dictionary including status (True/False), message, and created service name on success.
    """
    api = get_core_v1_api(config_path)

    # Build list of V1ServicePort objects based on input port configurations
    service_ports = []
    for p in ports:
        port_args = {
            "name": p.get("name"),
            "port": p["port"],
            "target_port": p.get("targetPort"),
            "protocol": p.get("protocol", "TCP")
        }
        if service_type == "NodePort" and "nodePort" in p:
            port_args["node_port"] = p["nodePort"]
        service_ports.append(client.V1ServicePort(**port_args))

    # Create the V1Service object with metadata and spec
    service = client.V1Service(
        metadata=client.V1ObjectMeta(name=service_name),
        spec=client.V1ServiceSpec(
            selector=selector or {},
            ports=service_ports,
            type=service_type
        )
    )

    try:
        resp = api.create_namespaced_service(namespace=namespace_name, body=service)
        return {
            "status": True,
            "message": f"Service '{service_name}' create success",
            "service": resp.metadata.name
        }
    except client.ApiException as e:
        if e.status in (409, 422):
            msg = f"Service '{service_name}' already exists"
        else:
            msg = f"Service create fail: {e}"
        return {"status": False, "message": msg}    
        
def delete_service(service_name: str, namespace_name: str, config_path: Optional[str] = None) -> bool:
    """
    Delete a Kubernetes Service by name in a specified namespace.

    Args:
        service_name (str): The name of the service to delete.
        namespace_name (str): The namespace where the service resides.
        config_path (Optional[str]): Path to the kubeconfig file.

    Returns:
        Dict[str, Any]: Dictionary indicating success status and a descriptive message.
    """
    api = get_core_v1_api(config_path)

    try:
        resp = api.delete_namespaced_service(name=service_name, namespace=namespace_name)
        return {"status": True, "message": f"Service '{resp}'"}
    except client.exceptions.ApiException as e:
        if e.status == 404:
            return {"status": False, "message": f"Service '{service_name}' not found."}
        else:
            return {"status": False, "message": f"Failed to delete service '{service_name}': {e}"}