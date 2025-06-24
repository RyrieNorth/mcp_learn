import subprocess

from typing import Optional

from utils.logger import logger
from utils.functions import timeit, handle_kube_error

class ResourcesDelete:
    def __init__(self, env: Optional[str]) -> None:
        self.env = env

    def kubectl_delete(
        self,
        resource_type: Optional[str],
        resource_name: Optional[str] = None,
        namespace: Optional[str] = None,
        output_type: Optional[str] = "name"
    ) -> str:
        """获取特定kubernetes资源后删除

        Args:
            resource_type (Optional[str]): 资源类型
            resource_name (Optional[str]): 资源名称
            namespace (Optional[str], optional): 资源所在的命名空间
            output_type (str, optional): 输出类型，默认为'name'

        Raises:
            RuntimeError: 当subprocess执行错误时抛出异常

        Returns:
            str: 纯文本
        """
        try:
            cmd = [
                "kubectl",
                "--kubeconfig", self.env,
                "delete", resource_type,
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
                logger.error(f"[kubectl_delete] Error running: {error_msg}")
                raise RuntimeError(error_msg)

            return stdout.decode().strip()

        except subprocess.SubprocessError as e:
            logger.error(f"[kubectl_delete] Subprocess error: {str(e)}")
            raise

    @handle_kube_error
    @timeit
    def delete_namespaces(
        self,
        namespaces: Optional[str]
    ) -> str:
        """删除命名空间

        Args:
            namespaces (Optional[str]): 命名空间名称

        Returns:
            str: 删除成功或失败信息
        """
        try:
            result = self.kubectl_delete("namespaces", resource_name=namespaces)
            if not result:
                return False
            return result
        except Exception as e:
            logger.error(f"[delete_namespaces] Failed to delete namespaces: {e}")
            return [e]

    @handle_kube_error
    @timeit
    def delete_services(
        self,
        services: Optional[str],
        namespace: Optional[str] = 'default',
    ) -> str:
        """删除services

        Args:
            services (Optional[str]): service名称
            namespace (Optional[str], optional): service所在的命名空间，默认为default

        Returns:
            str: 删除成功或失败信息
        """
        try:
            result = self.kubectl_delete("services", resource_name=services, namespace=namespace)
            if not result:
                return False
            return result
        except Exception as e:
            logger.error(f"[delete_services] Failed to delete services: {e}")
            return [e]

    @handle_kube_error
    @timeit
    def delete_pods(
        self,
        pod_name: Optional[str] = None,
        namespace: Optional[str] = 'default',
    ) -> str:
        """删除pod

        Args:
            pod_name (Optional[str], optional): pod名称
            namespace (Optional[str], optional): pod所在的命名空间，默认为default

        Returns:
            str: 删除成功或失败信息
        """
        try:
            result = self.kubectl_delete("pods", resource_name=pod_name, namespace=namespace)
            if not result:
                return False
            return result
        except Exception as e:
            logger.error(f"[delete_pods] Failed to delete pods: {e}")
            return [e]

    @handle_kube_error
    @timeit
    def delete_deployment_apps(
        self,
        app_name: Optional[str] = None,
        namespace: Optional[str] = 'default',
    ) -> str:
        """删除deployment.apps

        Args:
            app_name (Optional[str], optional): deployment名称
            namespace (Optional[str], optional): deployment所在的命名空间

        Returns:
            str: 删除成功或失败信息
        """
        try:
            result = self.kubectl_delete("deployments.app", resource_name=app_name, namespace=namespace)
            if not result:
                return False
            return result
        except Exception as e:
            logger.error(f"[delete_deployment_apps] Failed to delete deployment: {e}")
            return [e]