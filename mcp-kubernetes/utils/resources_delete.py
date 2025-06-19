import subprocess

from typing import Optional, Any

from utils.logger import logger

class ResourcesDelete:
    def __init__(self, env: Optional[str]) -> None:
        self.env = env

    def kubectl_delete(self, resource_type: Optional[str], resource_name: Optional[str] = None, namespace: Optional[str] = None, output_type: Optional[str] = "name") -> Any:
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
            
            
            
        except subprocess.SubprocessError as e:
            logger.error(f"[kubectl_get] Subprocess error: {str(e)}")
            raise
