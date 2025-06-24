import subprocess
import signal
import os
from typing import Optional, Dict, Any

from utils.logger import logger
from utils.functions import timeit, handle_kube_error


class PortForwarder:
    def __init__(self, env: Optional[str]) -> Any:
        self.env = env
        self.port_forward_processes: Dict[str, int] = {}

    def _make_key(
        self,
        resource_type: str,
        resource_name: str,
        local_port: int,
        remote_port: int,
        namespace: str
    ) -> str:
        return f"{namespace}/{resource_type}/{resource_name}:{local_port}->{remote_port}"

    @handle_kube_error
    @timeit
    def start_port_forward(
        self,
        resource_type: str,
        resource_name: str,
        local_port: int,
        remote_port: int,
        namespace: str = 'default'
    ) -> str:
        """映射本地端口到指定应用的端口

        Args:
            resource_type (str): 资源类型
            resource_name (str): 资源名称
            local_port (int): 本地端口
            remote_port (int): 远程端口
            namespace (str, optional): 资源所在的命名空间

        Returns:
            str: 进程pid描述
        """
        key = self._make_key(resource_type, resource_name, local_port, remote_port, namespace)

        cmd = [
            "kubectl",
            "--kubeconfig", self.env,
            "-n", namespace,
            "port-forward",
            "--address", "0.0.0.0,::",
            f"{resource_type}/{resource_name}",
            f"{local_port}:{remote_port}"
        ]

        logger.debug(f"Executing command: {cmd}")

        try:
            # 保活进程
            with open(os.devnull, 'a') as devnull:
                proc = subprocess.Popen(
                    cmd,
                    stdout=devnull,
                    stderr=devnull,
                    preexec_fn=os.setsid,
                    close_fds=True
                )
            self.port_forward_processes[key] = proc.pid
            logger.info(f"Started port-forward: {key}, PID: {proc.pid}")
            return f"Port-forward started in background with PID {proc.pid}"

        except Exception as e:
            logger.error(f"Failed to start port-forward {key}: {e}")
            return f"Failed to start port-forward: {str(e)}"

    @timeit
    def stop_port_forward(self, proc_id: Optional[int]) -> str:
        """停止端口转发进程

        Args:
            proc_id (Optional[int]): 进程id

        Returns:
            str: 进程关闭情况
        """
        if proc_id is None:
            return "No PID provided to stop port-forward"

        try:
            os.killpg(os.getpgid(proc_id), signal.SIGTERM)
            logger.info(f"Stopped port-forward for PID {proc_id}")
            return f"Port-forward stopped (PID {proc_id})"
        except Exception as e:
            logger.error(f"Failed to stop port-forward PID {proc_id}: {e}")
            return f"Failed to stop port-forward: {str(e)}"
