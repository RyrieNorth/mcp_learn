import time
from utils.debug import is_debug_mode
from utils.logger import logger
from typing import List, Optional, Dict, Any
from kubernetes import client
from core.client_manager import get_core_v1_api


def list_namespaces(config_path: Optional[str] = None) -> List[str]:
    api = get_core_v1_api(config_path)
    return [ns.metadata.name for ns in api.list_namespace().items]


def namespace_detail(ns_name: str, config_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    api = get_core_v1_api(config_path)
    for ns in api.list_namespace().items:
        if ns.metadata.name == ns_name:
            return {
                "namespace_name": ns.metadata.name,
                "labels": ns.metadata.labels or {},
            }


def create_namespace(ns_name: str, label: Optional[str] = None, config_path: Optional[str] = None) -> Dict[str, Any]:
    api = get_core_v1_api(config_path)

    labels = {}
    if label:
        try:
            key, value = label.split("=", 1)
            labels[key.strip()] = value.strip()
        except ValueError:
            return {"status": False, "message": f"Label format error!, should key=value, not：{label}"}

    try:
        resp = api.create_namespace(
            body=client.V1Namespace(
                metadata=client.V1ObjectMeta(name=ns_name, labels=labels if labels else None)
            )
        )
        return {
            "status": True,
            "message": f"Namespace '{ns_name}' create success!",
            "namespace": resp.metadata.name
        }
    except client.exceptions.ApiException as e:
        if e.status == 409:
            return {
                "status": False,
                "message": f"Namespace '{ns_name}' alreay exists."
            }
        else:
            return {
                "status": False,
                "message": f"Create fail: {e}"
            }

def delete_namespace(ns_name: str, timeout: int = 60, config_path: Optional[str] = None) -> bool:
    api = get_core_v1_api(config_path)

    try:
        api.delete_namespace(name=ns_name)
    except client.exceptions.ApiException as e:
        if e.status == 404:
            return {"status": False, "message": f"Namespace '{ns_name}' not found."}
        else:
            return {"status": False, "message": f"Failed to delete namespace '{ns_name}': {e}"}

    # Wait for namespace to be fully deleted
    for _ in range(timeout):
        try:
            api.read_namespace(name=ns_name)
            time.sleep(1)
        except client.exceptions.ApiException as e:
            if e.status == 404:
                return {"status": True, "message": f"Namespace '{ns_name}' deleted successfully."}
            else:
                return {"status": False, "message": f"Error while checking namespace deletion status: {e}"}

    return {"status": False, "message": f"Timeout: Namespace '{ns_name}' still exists after {timeout} seconds."}
