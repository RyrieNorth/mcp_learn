import subprocess

from typing import Optional, Any, List, Dict

from utils.logger import logger
from utils.functions import timeit, handle_kube_error

class ResouecesDescribe:
    def __init__(self, env: Optional[str]) -> None:
        self.env = env
        
    def kubectl_describe(
        self,
        resource_type: Optional[str],
        resource_name: Optional[str] = None,
        namespace: Optional[str] = None,
        all_namespace: Optional[bool] = False,
    ) -> Any:
        """获取特定kubernetes资源，并结构化输出

        Args:
            resource_type (Optional[str]): 资源类型
            resource_name (Optional[str]): 资源名称
            namespace (Optional[str], optional): 资源所在的命名空间
            all_namespace (Optional[bool]): 当设定为True时，则列出所有命名空间下对应的资源，反之仅列出'default'命名空间下的资源
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
                "describe", resource_type,
            ]
            if namespace:
                cmd += ["-n", namespace]
                
            if resource_name:
                cmd += [resource_name]

            if all_namespace:
                cmd += ["--all-namespaces"]

            logger.debug(f"Exec cmd: {cmd}")
            
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = proc.communicate()

            if proc.returncode != 0:
                error_msg = stderr.decode().strip()
                logger.error(f"[kubectl_describe] Error running: {error_msg}")
                raise RuntimeError(error_msg)

            return stdout.decode().strip()

        except subprocess.SubprocessError as e:
            logger.error(f"[kubectl_describe] Subprocess error: {str(e)}")
            raise

    @handle_kube_error
    @timeit
    def describe_nodes(
        self,
        node_name: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """描述nodes信息

        Args:
            node_name (Optional[str], optional): 节点名称，当该值为空，则列出所有

        Returns:
            List[Dict[str, Any]]: 节点信息
        """
        try:
            if node_name:
                raw_result = self.kubectl_describe("nodes", resource_name=node_name)
            else:
                raw_result = self.kubectl_describe("nodes")
                
            return [{"raw": raw_result}]
                
        except Exception as e:
            logger.error(f"[describe_nodes] Failed to describe nodes: {e}")
            return [e]
        
    @handle_kube_error
    @timeit
    def describe_namespaces(
        self,
        namespace: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """描述namespaces信息

        Args:
            namespaces (Optional[str], optional): 命名空间名称，当该值为空，则列出所有

        Returns:
            List[Dict[str, Any]]: 命名空间信息
        """
        try:
            if namespace:
                raw_result = self.kubectl_describe("namespaces", resource_name=namespace)
            else:
                raw_result = self.kubectl_describe("namespaces")
                
            return [{"raw": raw_result}]
                
        except Exception as e:
            logger.error(f"[describe_namespaces] Failed to describe namespaces: {e}")
            return [e]
        
    @handle_kube_error
    @timeit
    def describe_services(
        self,
        service: Optional[str] = None,
        namespace: Optional[str] = None,
        all_namespace: Optional[bool] = False,
    ) -> List[Dict[str, Any]]:
        """描述services信息

        Args:
            service (Optional[str], optional): services名称，当该值为空，则列出所有
            all_namespace (Optional[bool]): 当设定为True时，则列出所有命名空间下对应的资源，反之仅列出'default'命名空间下的资源

        Returns:
            List[Dict[str, Any]]: services信息
        """
        try:
            if service:
                raw_result = self.kubectl_describe(
                    "services",
                    resource_name=service,
                    namespace=namespace,
                    all_namespace=all_namespace,
                )
            else:
                raw_result = self.kubectl_describe("services", all_namespace=all_namespace)
                
            return [{"raw": raw_result}]
                
        except Exception as e:
            logger.error(f"[describe_services] Failed to describe services: {e}")
            return [e]
        
    @handle_kube_error
    @timeit
    def describe_pods(
        self,
        pod_name: Optional[str] = None,
        namespace: Optional[str] = None,
        all_namespace: Optional[bool] = False,
    ) -> List[Dict[str, Any]]:
        """描述pods信息

        Args:
            pod_name (Optional[str], optional): pods名称，当该值为空，则列出所有
            namespace (Optional[str], optional): pods所在的命名空间，默认为default
            all_namespace (Optional[bool]): 当设定为True时，则列出所有命名空间下对应的资源，反之仅列出'default'命名空间下的资源

        Returns:
            List[Dict[str, Any]]: pods信息
        """
        try:
            if pod_name:
                raw_result = self.kubectl_describe(
                    "pods",
                    resource_name=pod_name,
                    namespace=namespace,
                    all_namespace=all_namespace
                )
            else:
                raw_result = self.kubectl_describe("pods", all_namespace=all_namespace)
                
            return [{"raw": raw_result}]
                
        except Exception as e:
            logger.error(f"[describe_pods] Failed to describe pods: {e}")
            return [e]

    @handle_kube_error
    @timeit
    def describe_deployments(
        self,
        app_name: Optional[str] = None,
        namespaces: Optional[str] = None,
        all_namespace: Optional[bool] = False,
    ) -> List[Dict[str, Any]]:
        """描述deployments信息

        Args:
            app_name (Optional[str], optional): deployment名称，当该值为空，则列出所有
            namespace (Optional[str], optional): deployment所在的命名空间，默认为default
            all_namespace (Optional[bool]): 当设定为True时，则列出所有命名空间下对应的资源，反之仅列出'default'命名空间下的资源

        Returns:
            List[Dict[str, Any]]: deployment信息
        """
        try:
            if app_name:
                raw_result = self.kubectl_describe(
                    "deployments.app",
                    resource_name=app_name,
                    namespace=namespaces,
                    all_namespace=all_namespace
                )
            else:
                raw_result = self.kubectl_describe("deployments.app", all_namespace=all_namespace)
                
            return [{"raw": raw_result}]
                
        except Exception as e:
            logger.error(f"[describe_deployments] Failed to describe deployments: {e}")
            return [e]
