import subprocess

from typing import Optional, Any, List, Dict

from utils.logger import logger
from utils.functions import timeit, handle_kube_error

class ResourceLog:
    def __init__(self, env: Optional[str] = None) -> None:
        self.env = env

    def _run_command(self, cmd: List[str]) -> str:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            raise subprocess.SubprocessError(result.stderr.strip())
        return result.stdout.strip()

    def _get_pod_name(self, namespace: str, selector: str) -> str:
        cmd = [
            "kubectl", "--kubeconfig", self.env,
            "-n", namespace,
            "get", "pods",
            "-l", selector,
            "-o", "jsonpath={.items[0].metadata.name}"
        ]
        return self._run_command(cmd)

    def _resolve_pod_name(self, resource_type: str, resource_name: str, namespace: str, label_selector: Optional[str]) -> str:
        if resource_type == "pod":
            return resource_name

        if label_selector:
            return self._get_pod_name(namespace, label_selector)

        # 自动推测 labelSelector
        label_key = {
            "deployment": "app",
            "job": "job-name",
            "cronjob": "job-name"  # CronJob 创建 Job，再找 Job 的 pod
        }.get(resource_type)

        if not label_key:
            raise ValueError(f"Unsupported resource type for pod lookup: {resource_type}")

        selector = f"{label_key}={resource_name}"
        return self._get_pod_name(namespace, selector)

    @handle_kube_error
    @timeit
    def kubectl_logs(
        self,
        resource_type: Optional[str],
        resource_name: Optional[str] = None,
        namespace: Optional[str] = 'default',
        container: Optional[str] = None,
        tail: Optional[str] = None,
        since: Optional[str] = None,
        sinceTime: Optional[str] = None,
        timestamps: Optional[bool] = False,
        previous: Optional[bool] = False,
        labelSelector: Optional[str] = None
    ) -> str:
        """获取特定资源日志

        Args:
            resource_type (Optional[str]): 资源类型，支持："pod", "deployment", "job", "cronjob"
            resource_name (Optional[str], optional): 资源名称
            namespace (Optional[str], optional): 资源所在的命名空间
            container (Optional[str], optional): 资源对应的容器
            tail (Optional[str], optional): 从日志末尾输出对应的行数
            since (Optional[str], optional): 显示自多长时间一来的信息，例如：（5s, 1m, 1h）
            sinceTime (Optional[str], optional): 显示相对时间以来的日志（RFC3339）
            timestamps (Optional[bool], optional): 是否显示日志时间戳
            previous (Optional[bool], optional): 是否包含容器退出日志
            labelSelector (Optional[str], optional): 根据标签选择器过滤资源

        Returns:
            str: 资源日志信息
        """
        try:
            if resource_type not in ("pod", "deployment", "job", "cronjob"):
                raise ValueError(f"Unsupported resource type: {resource_type}")

            pod_name = self._resolve_pod_name(resource_type, resource_name, namespace, labelSelector)

            cmd = [
                "kubectl", "--kubeconfig", self.env,
                "-n", namespace,
                "logs", pod_name
            ]

            if container:
                cmd += ["-c", container]
            if tail:
                cmd += ["--tail", tail]
            if since:
                cmd += ["--since", since]
            if sinceTime:
                cmd += ["--since-time", sinceTime]
            if timestamps:
                cmd.append("--timestamps")
            if previous:
                cmd.append("--previous")

            logger.debug(f"[kubectl_logs] Exec cmd: {' '.join(cmd)}")
            return self._run_command(cmd)

        except subprocess.SubprocessError as e:
            logger.error(f"[kubectl_logs] Subprocess error: {str(e)}")
            return str(e)
        except Exception as e:
            logger.error(f"[kubectl_logs] Error: {str(e)}")
            return str(e)
