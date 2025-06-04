from kubernetes import client, config
from kubernetes.client import ApiClient
from typing import Optional


def get_k8s_client(config_path: Optional[str] = None) -> ApiClient:
    try:
        if config_path:
            config.load_kube_config(config_file=config_path)
        else:
            try:
                config.load_kube_config()  # Try default local config
            except Exception:
                config.load_incluster_config()  # Fallback for in-cluster execution
    except Exception as e:
        raise RuntimeError(f"Failed to load Kubernetes configuration: {e}")
    
    return client.ApiClient()


def get_core_v1_api(config_path: Optional[str] = None) -> client.CoreV1Api:
    api_client = get_k8s_client(config_path)
    return client.CoreV1Api(api_client=api_client)