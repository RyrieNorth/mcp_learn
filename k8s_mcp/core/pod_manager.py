from typing import List, Optional, Dict, Any
from core.client_manager import get_core_v1_api
from kubernetes import client


def pod_list(config_path: Optional[str] = None) -> List[str]:
    """
    Retrieve a list of all pod names across all namespaces in the cluster.

    Args:
        config_path (Optional[str]): Optional kubeconfig file path.

    Returns:
        List[str]: List of pod names.
    """
    api = get_core_v1_api(config_path)
    return [pod.metadata.name for pod in api.list_pod_for_all_namespaces().items]


def pod_detail(pod_name: str, namespace_name: str = None, config_path: Optional[str] = None) -> Optional[dict]:
    """
    Fetch detailed information about a specific pod by its name or namespace.

    Args:
        pod_name (str): Name of the pod.
        namespace_name (str, optional): Namespace the pod belongs to.
        config_path (Optional[str]): Optional kubeconfig file path.

    Returns:
        Optional[dict]: Dictionary with pod details such as host IP, node, state, pod IP,
                        namespace, container names and images, or None if pod not found.
    """
    api = get_core_v1_api(config_path)
    for pod in api.list_pod_for_all_namespaces().items:
        if pod.metadata.name == pod_name or pod.metadata.namespace == namespace_name:
            return {
                "running_on": pod.status.host_ip,
                "running_node": pod.spec.node_name,
                "state": pod.status.phase,
                "pod_ip": pod.status.pod_ip,
                "namespace": pod.metadata.namespace,
                "name": pod.metadata.name,
                "containers": [
                    {
                        "name": container.name,
                        "image": container.image,
                    } for container in pod.spec.containers
                ],
            }
    return None


def create_pod(
    pod_name: str,
    namespace_name: str,
    container_names: List[Dict[str, Any]],
    volumes: Optional[List[Dict[str, Any]]] = None,
    labels: Optional[Dict[str, str]] = None,
    config_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a pod in a specified namespace with given containers, volumes, and labels.

    Args:
        pod_name (str): Name of the pod to create.
        namespace_name (str): Namespace where the pod will be created.
        container_names (List[Dict[str, Any]]): List of container specifications.
            Each container dict can include:
                - "name" (str): Container name.
                - "image" (str): Container image.
                - "ports" (List[Dict[str, Any]]): Container ports.
                - "env" (Dict[str, str]): Environment variables.
                - "volume_mounts" (List[Dict[str, str]]): Volume mounts.
                - "imagePullPolicy" (str, optional): Image pull policy.
        volumes (Optional[List[Dict[str, Any]]]): Optional list of volume specs.
        labels (Optional[Dict[str, str]]): Optional labels for the pod metadata.
        config_path (Optional[str]): Optional kubeconfig file path.

    Returns:
        Dict[str, Any]: Status of pod creation, including pod name, namespace, or error message.
    """
    api = get_core_v1_api(config_path)

    containers = []
    for c in container_names:
        ports = [
            client.V1ContainerPort(
                container_port=p["containerPort"],
                protocol=p.get("protocol", "TCP")
            ) for p in c.get("ports", [])
        ]

        envs = [
            client.V1EnvVar(name=k, value=v)
            for k, v in c.get("env", {}).items()
        ]

        mounts = [
            client.V1VolumeMount(
                name=m["name"],
                mount_path=m["mountPath"]
            ) for m in c.get("volume_mounts", [])
        ]

        container = client.V1Container(
            name=c["name"],
            image=c["image"],
            ports=ports,
            env=envs,
            volume_mounts=mounts,
            image_pull_policy=c.get("imagePullPolicy", "IfNotPresent")
        )
        containers.append(container)

    volume_objs = []
    for v in volumes or []:
        vol = client.V1Volume(name=v["name"])
        if "emptyDir" in v:
            vol.empty_dir = client.V1EmptyDirVolumeSource()
        if "hostPath" in v:
            vol.host_path = client.V1HostPathVolumeSource(**v["hostPath"])
        volume_objs.append(vol)

    pod_spec = client.V1PodSpec(containers=containers, volumes=volume_objs or None)
    pod_metadata = client.V1ObjectMeta(name=pod_name, labels=labels or {})

    pod = client.V1Pod(metadata=pod_metadata, spec=pod_spec)
    try:
        api_response = api.create_namespaced_pod(namespace=namespace_name, body=pod)
        return {
            "status": api_response.status.phase,
            "pod_name": api_response.metadata.name,
            "namespace": api_response.metadata.namespace
        }
    except client.ApiException as e:
        if e.status in (409, 422):
            msg = f"Pod '{pod_name}' already exists"
        else:
            msg = f"Pod create fail: {e}"
        return {"status": False, "message": msg}
    

def delete_pod(pod_name: str, namespace_name: str, config_path: Optional[str] = None) -> bool:
    """
    Delete a specified pod from a given namespace.

    Args:
        pod_name (str): Name of the pod to delete.
        namespace_name (str): Namespace where the pod exists.
        config_path (Optional[str]): Optional kubeconfig file path.

    Returns:
        bool: True if deletion was successful, False otherwise with error message.
    """
    api = get_core_v1_api(config_path)

    try:
        resp = api.delete_namespaced_pod(name=pod_name, namespace=namespace_name)
        return {"status": True, "message": f"Pod: '{resp}'"}
    except client.ApiException as e:
        if e.status == 404:
            return {"status": False, "message": f"Pod '{pod_name}' not found."}
        else:
            return {"status": False, "message": f"Failed to delete pod '{pod_name}': {e}"}