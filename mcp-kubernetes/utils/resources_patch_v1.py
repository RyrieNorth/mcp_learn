import subprocess
import json
from typing import Optional, List
from utils.logger import logger
from utils.functions import handle_kube_error

class ResourcePatch:
    def __init__(self, env: Optional[str] = None) -> None:
        self.env = env
        
    def kubectl_patch(
        self,
        resource_type: str,
        resource_name: str,
        patch: dict,
        namespace: str = "default",
        patch_type: str = "strategic"  # 可选: strategic, merge, json
    ) -> str:
        """
        使用 kubectl patch 修改 Kubernetes 资源。

        Args:
            resource_type (str): 资源类型，如 deployment、pod、service。
            resource_name (str): 资源名称。
            patch (dict): patch 内容，必须是 dict。
            namespace (str): 命名空间，默认 default。
            patch_type (str): patch 类型，可为 strategic、merge、json。

        Returns:
            str: patch 执行结果或错误信息。
        """
        try:
            patch_str = json.dumps(patch)
            cmd = [
                "kubectl", "--kubeconfig", self.env,
                "-n", namespace,
                "patch", resource_type, resource_name,
                f"--type={patch_type}",
                f"-p={patch_str}"
            ]

            logger.debug(f"Executing command: {' '.join(cmd)}")
            result = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
            return result.strip()
        except subprocess.CalledProcessError as e:
            logger.error(f"[kubectl_patch] Error: {e.output}")
            return handle_kube_error(e.output)