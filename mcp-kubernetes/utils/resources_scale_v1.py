import subprocess

from typing import Optional, Any

from utils.logger import logger
from utils.functions import timeit, handle_kube_error

class ResourceScale:
    def __init__(self, env: Optional[str] = None) -> None:
        self.env = env

    @handle_kube_error
    @timeit
    def kubectl_scale_resources(
        self,
        resource_name: Optional[str],
        replicas: Optional[str],
        namespace: Optional[str] = 'default',
        resource_type: Optional[str] = None,
    ) -> Any:
        """扩建或缩减副本

        Args:
            resource_name (Optional[str]): 资源名称
            replicas (Optional[str]): 副本数量
            namespace (Optional[str], optional): 资源所在命名空间，默认为default
            resource_type (Optional[str], optional): 资源类型，目前支持：deployment, replicaset, statefulset

        Returns:
            Any: 回调结果
        """
        try:
            cmd = [
                "kubectl",
                "--kubeconfig", self.env,
                "scale",
                "--replicas", replicas,
                resource_type,
                resource_name
            ]
            
            if namespace:
                cmd += ["-n", namespace]
                
            if resource_type not in ('deployment', 'replicaset', 'statefulset'):
                raise ValueError(f"Unsupport resource type: {resource_type}")
            
            logger.debug(f"Exec cmd: {cmd}")
            
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = proc.communicate()

            if proc.returncode != 0:
                error_msg = stderr.decode().strip()
                logger.error(f"[kubectl_scale_resources] Error running: {error_msg}")
                raise RuntimeError(error_msg)

            return stdout.decode().strip()
        
        except subprocess.SubprocessError as e:
            logger.error(f"[kubectl_scale_resources] Subprocess error: {str(e)}")
            return [e]