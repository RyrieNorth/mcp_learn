from utils.logger import logger
from typing import List, Optional, Dict, Any
from kubernetes import client
from core.client_manager import get_core_v1_api


def service_list(config_path: Optional[str] = None) -> List[str]:
    api = get_core_v1_api(config_path=config_path)
    logger.info("Fetch all services...")
    return [svc.metadata.name for svc in api.list_service_for_all_namespaces().items]


def service_detail(service_name: str, namespace_name: str = None, config_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    api = get_core_v1_api(config_path)
    logger.info("Fetch service details...")
    for svc in api.list_service_for_all_namespaces().items:
        if svc.metadata.name == service_name or svc.metadata.namespace == namespace_name:
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
    api = get_core_v1_api(config_path)

    # 构建 V1ServicePort 列表
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

    # 构建 Service 对象
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
    api = get_core_v1_api(config_path)

    try:
        resp = api.delete_namespaced_service(name=service_name, namespace=namespace_name)
        return {"status": True, "message": f"Service '{resp}'"}
    except client.exceptions.ApiException as e:
        if e.status == 404:
            return {"status": False, "message": f"Service '{service_name}' not found."}
        else:
            return {"status": False, "message": f"Failed to delete service '{service_name}': {e}"}