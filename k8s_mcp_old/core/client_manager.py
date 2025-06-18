from kubernetes import client, config
from kubernetes.client import ApiClient
from typing import Optional


def get_k8s_client(config_path: Optional[str] = None) -> ApiClient:
    """
    Initialize and return a Kubernetes API client.

    Attempts to load the Kubernetes configuration from the specified kubeconfig file.
    If no file path is provided, it tries the default local kubeconfig. If that fails,
    it falls back to in-cluster configuration, which is used when running inside a pod.

    Args:
        config_path (Optional[str]): Path to the kubeconfig file. If None, use default or in-cluster config.

    Returns:
        ApiClient: An instance of Kubernetes ApiClient.

    Raises:
        RuntimeError: If loading the Kubernetes configuration fails.
    """
    try:
        if config_path:
            config.load_kube_config(config_file=config_path)
        else:
            try:
                config.load_kube_config()  # Try default local kubeconfig
            except Exception:
                config.load_incluster_config()  # Fallback to in-cluster config
    except Exception as e:
        raise RuntimeError(f"Failed to load Kubernetes configuration: {e}")

    return client.ApiClient()


def get_core_v1_api(config_path: Optional[str] = None) -> client.CoreV1Api:
    """
    Create and return a CoreV1Api client for Kubernetes Core API operations.

    Args:
        config_path (Optional[str]): Optional path to kubeconfig file.

    Returns:
        CoreV1Api: Kubernetes CoreV1Api client instance.
    """
    api_client = get_k8s_client(config_path)
    return client.CoreV1Api(api_client=api_client)
