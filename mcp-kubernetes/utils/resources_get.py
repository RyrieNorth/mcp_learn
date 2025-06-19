import subprocess
import json
import yaml

from typing import Optional, Any, List, Dict

from utils.logger import logger
from utils.functions import timeit, handle_kube_error


def format_image_list(images: List[Dict]) -> Dict[str, any]:
    formatted = []

    for image in images:
        tag_names = [name for name in image.get("names", []) if ":" in name and "@" not in name]
        if tag_names:
            formatted.append({
                "name": tag_names[0],
                "sizeBytes": image.get("sizeBytes", 0)
            })

    return {
        "total": len(formatted),
        "list": formatted
    }

class ResouecesGet:
    def __init__(self, env: Optional[str]) -> None:
        self.env = env

    @handle_kube_error
    @timeit
    def kubectl_get(self, resource_type: Optional[str], resource_name: Optional[str] = None, namespace: Optional[str] = None, output_type: Optional[str] = "json") -> Any:
        """获取特定kubernetes资源，并结构化输出

        Args:
            resource_type (Optional[str]): 资源类型
            resource_name (Optional[str]): 资源名称
            namespace (Optional[str], optional): 资源所在的命名空间
            output_type (str, optional): 输出类型，默认为'json'

        Raises:
            RuntimeError: 当subprocess执行错误时抛出异常

        Returns:
            Any: 返回Dict或纯文本
        """
        try:
            cmd = [
                "kubectl",
                "--kubeconfig", self.env,
                "get", resource_type,
                "-o", output_type
            ]
            if namespace:
                cmd += ["-n", namespace]
                
            if resource_name:
                cmd += [resource_name]

            logger.debug(f"Exec cmd: {cmd}")
            
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = proc.communicate()

            if proc.returncode != 0:
                error_msg = stderr.decode().strip()
                logger.error(f"[kubectl_get] Error running {' '.join(cmd)}: {error_msg}")
                raise RuntimeError(error_msg)

            output = stdout.decode().strip()

            if output_type == "json":
                return json.loads(output)
            return output

        except subprocess.SubprocessError as e:
            logger.error(f"[kubectl_get] Subprocess error: {str(e)}")
            raise

        except json.JSONDecodeError as je:
            logger.error(f"[kubectl_get] Failed to parse JSON: {je}")
            raise

    @handle_kube_error
    @timeit
    def get_nodes(self, node_name: Optional[str] = None, output_type: Optional[str] = "json") -> List[Dict[str, Any]]:
        """获取kubernetes节点信息

        Args:
            node_name (Optional[str], optional): 节点名称，当该值为空，则列出所有
            output_type (Optional[str], optional): 输出类型，默认为json

        Returns:
            List[Dict[str, Any]]: 节点信息
        """
        try:
            if node_name:
                raw_result = self.kubectl_get("nodes", resource_name=node_name, output_type=output_type)
            else:
                raw_result = self.kubectl_get("nodes", output_type=output_type)

            if output_type == "yaml":
                try:
                    result = yaml.safe_load(raw_result)
                except yaml.YAMLError as ye:
                    logger.error(f"[get_nodes] YAML parse error: {ye}")
                    return []
            elif output_type == "json":
                result = raw_result
            else:
                return [{"raw": raw_result}]

            if node_name:
                result = {"items": [result]}
                
            items = result.get("items", [])
            nodes = []
            
            for node in items:
                metadata = node.get("metadata", {})
                spec = node.get("spec", {})
                status = node.get("status", {})

                name = metadata.get("name", "")

                addresses = status.get("addresses", [])
                nodeinfo = status.get("nodeInfo", {})
                images = status.get("images", [])

                nodes.append({
                    "name": name,
                    "labels": metadata.get("labels", {}),

                    "taints": spec.get("taints", []),
                    "pod_cidr": spec.get("podCIDR"),
                    "pod_cidrs": spec.get("podCIDRs", []),
                    "addresses": [
                        {
                            "type": addr.get("type"),
                            "address": addr.get("address")
                        } for addr in addresses
                    ],

                    "capacity": status.get("capacity", {}),
                    "allocatable": status.get("allocatable", {}),

                    "os_release": nodeinfo.get("osImage"),
                    "kernel_version": nodeinfo.get("kernelVersion"),
                    "container_runtime": nodeinfo.get("containerRuntimeVersion"),
                    "kubelet_version": nodeinfo.get("kubeletVersion"),
                    "kube_proxy_version": nodeinfo.get("kubeProxyVersion"),

                    "images": format_image_list(images)
                })

            return nodes
        
        except Exception as e:
            logger.error(f"[get_nodes] Failed to get nodes: {e}")
            return []

    @handle_kube_error
    @timeit
    def get_namespaces(self, namespace: Optional[str] = None, output_type: Optional[str] = "json") -> List[Dict[str, Any]]:
        """获取命名空间信息

        Args:
            namespace (Optional[str], optional): 命名空间名称，当该值为空，则列出所有
            output_type (str, optional): 输出类型，默认为json

        Returns:
            List[Dict[str, Any]]: 命名空间信息
        """
        try:
            if namespace:
                raw_result = self.kubectl_get("namespaces", resource_name=namespace, output_type=output_type)
            else:
                raw_result = self.kubectl_get("namespaces", output_type=output_type)

            if output_type == "yaml":
                try:
                    result = yaml.safe_load(raw_result)
                except yaml.YAMLError as ye:
                    logger.error(f"[get_namespaces] YAML parse error: {ye}")
                    return []
            elif output_type == "json":
                result = raw_result
            else:
                return [{"raw": raw_result}]

            if namespace:
                result = {"items": [result]}
                
            items = result.get("items", [])
            namespaces = []

            for ns in items:
                metadata = ns.get("metadata", {})
                status = ns.get("status", {})
                name = metadata.get("name", {})

                if namespace and name != namespace:
                    continue
                
                namespaces.append({
                    "name": metadata.get("name"),
                    "labels": metadata.get("labels", {}),
                    "status": status.get("phase")
                })

            return namespaces

        except Exception as e:
            logger.error(f"[get_namespaces] Failed to get namespaces: {e}")
            return []

    @handle_kube_error
    @timeit 
    def get_services(self, service: Optional[str] = None, namespace: Optional[str] = "default", output_type: Optional[str] = "json") -> List[Dict[str, Any]]:
        """获取service信息

        Args:
            service (Optional[str], optional): service名称，当该值为空，则列出所有
            namespace (Optional[str], optional): service所在的命名空间，默认为default
            output_type (Optional[str], optional): 输出类型，默认为json

        Returns:
            List[Dict[str, Any]]: service信息
        """
        try:
            if service:
                raw_result = self.kubectl_get("services", namespace=namespace, resource_name=service, output_type=output_type)
            else:
                raw_result = self.kubectl_get("services", namespace=namespace, output_type=output_type)

            if output_type == "yaml":
                try:
                    result = yaml.safe_load(raw_result)
                except yaml.YAMLError as ye:
                    logger.error(f"[get_services] YAML parse error: {ye}")
                    return []
                
            elif output_type == "json":
                result = raw_result
                
            else:
                return [{"raw": raw_result}]

            if service:
                result = {"items": [result]}
                
            items = result.get("items", [])
            services = []

            for svc in items:
                metadata = svc.get("metadata", {})
                spec = svc.get("spec", {})
                ports = spec.get("ports", {})
                name = metadata.get("name", {})

                if service and name != service:
                    continue
                
                services.append({
                    "name": metadata.get("name"),
                    "namespace": metadata.get("namespace"),
                    "labels": metadata.get("labels", {}),
                    "selector": spec.get("selector", {}),
                    "type": spec.get("type"),
                    "cluster_ip": spec.get("clusterIP"),
                    "cluster_ips": spec.get("clusterIPs", {}),
                    "ports": [
                        {
                            "name": port.get("name"),
                            "nodePort": port.get("nodePort", {}),
                            "port": port.get("port"),
                            "protocol": port.get("protocol"),
                            "targetPort": port.get("targetPort")
                        } for port in ports
                    ],
                })

            return services

        except Exception as e:
            logger.error(f"[get_services] Failed to get services: {e}")
            return []

    @handle_kube_error
    @timeit
    def get_pods(self, pod_name: Optional[str] = None, namespace: Optional[str] = "default", output_type: Optional[str] = "json") -> List[Dict[str, Any]]:
        """获取pod信息

        Args:
            pod_name (Optional[str], optional): pod名称，当该值为空，则列出所有
            namespace (Optional[str], optional): pod所在的命名空间，默认为default
            output_type (Optional[str], optional): 输出类型，默认为json

        Returns:
            List[Dict[str, Any]]: pod信息
        """
        try:
            if pod_name:
                raw_result = self.kubectl_get("pods", namespace=namespace, resource_name=pod_name, output_type=output_type)
            else:
                raw_result = self.kubectl_get("pods", namespace=namespace, output_type=output_type)

            if output_type == "yaml":
                try:
                    result = yaml.safe_load(raw_result)
                except yaml.YAMLError as ye:
                    logger.error(f"[get_pods] YAML parse error: {ye}")
                    return []
            elif output_type == "json":
                result = raw_result
            else:
                return [{"raw": raw_result}]

            if pod_name:
                result = {"items": [result]}
                
            items = result.get("items", [])
            pods = []
            
            for pod in items:
                metadata = pod.get("metadata", {})
                status = pod.get("status", {})
                spec = pod.get("spec", {})

                pods.append({
                    "name": metadata.get("name"),
                    "namespace": metadata.get("namespace"),
                    "labels": metadata.get("labels", {}),
                    "restart": spec.get("restartPolicy"),
                    "running_on": status.get("hostIP"),
                    "running_node": spec.get("nodeName"),
                    "state": status.get("phase"),
                    "pod_ip": status.get("podIP"),
                    "containers": [
                        {
                            "name": c.get("name"),
                            "image": c.get("image"),
                            "volume_mounts": [
                                {
                                    "total": len(c.get("volumeMounts", [])),
                                    "details": c.get("volumeMounts", [])
                                }    
                            ],
                        } for c in spec.get("containers", [])
                    ],
                    "volumes": [
                        {
                            "total": len(spec.get("volumes", [])),
                            "details": spec.get("volumes", [])
                        }
                    ]
                })

            return pods

        except Exception as e:
            logger.error(f"[get_pods] Failed to get pods: {e}")
            return []

    @handle_kube_error
    @timeit
    def get_deployment_apps(self, app_name: Optional[str] = None, namespace: Optional[str] = 'default', output_type: Optional[str] = 'json') -> List[Dict[str, Any]]:
        """获取deployment信息

        Args:
            app_name (Optional[str], optional): deployment名称，当该值为空，则列出所有
            namespace (Optional[str], optional): deployment所在的命名空间
            output_type (Optional[str], optional): 输出类型，默认为json

        Returns:
            List[Dict[str, Any]]: _description_
        """
        try:
            if app_name:
                raw_result = self.kubectl_get("deployments.app", namespace=namespace, resource_name=app_name, output_type=output_type)
            else:
                raw_result = self.kubectl_get("deployments.app", namespace=namespace, output_type=output_type)
                
            if output_type == "yaml":
                try:
                    result = yaml.safe_load(raw_result)
                except yaml.YAMLError as ye:
                    logger.error(f"[get_deployment_apps] YAML parse error: {ye}")
                    return []
                
            elif output_type == "json":
                result = raw_result
            
            else:
                return [{"raw": raw_result}]
            
            if app_name:
                result = {"items": [result]}
            
            items = result.get("items", [])
            apps = []
            
            for app in items:
                metadata = app.get("metadata", {})
                spec = app.get("spec", {})
                status = app.get("status", {})
                template = spec.get("template", {})
                template_spec = template.get("spec", {})
                
                apps.append({
                    "name": metadata.get("name"),
                    "namespace": metadata.get("namespace"),
                    "labels": metadata.get("labels", {}),
                    "replicas": spec.get("replicas"),
                    "selector": spec.get("selector"),
                    "restart": template_spec.get("restartPolicy"),
                    "containers": [
                        {
                            "name": c.get("name"),
                            "image": c.get("image"),
                            "volume_mounts": [
                                {
                                    "total": len(c.get("volumeMounts", [])),
                                    "details": c.get("volumeMounts", [])
                                }    
                            ],
                            "ports": [
                                {
                                    "total": len(c.get("ports", [])),
                                    "details": c.get("ports", [])
                                }
                            ],
                        } for c in template_spec.get("containers", [])
                    ],
                    "volumes": [
                        {
                            "total": len(template_spec.get("volumes", [])),
                            "details": template_spec.get("volumes", [])
                        }
                    ],
                    "available_replicas": status.get("availableReplicas"),
                    "ready_replicas": status.get("readyReplicas")
                })
            return apps
                
        except Exception as e:
            logger.error(f"[get_deployment_apps] Failed to get apps: {e}")
            return []



# if __name__ == "__main__":
    # print(kubectl_get("ns", "", "wide"))
    # print(get_nodes("k8s-master.ryrie.cn", output_type="json"))
    # pprint(get_namespaces("ryrie",output_type="json"))
    # pprint(get_services("ryrie", "", output_type="json"))
    # pprint(get_pods("", namespace="kube-system", output_type="json"))
    # pprint(get_deployment_apps("coredns", namespace="kube-system", output_type="json"))