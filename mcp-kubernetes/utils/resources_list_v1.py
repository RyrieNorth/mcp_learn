import subprocess

from typing import Optional, Any, List, Dict

from utils.logger import logger
from utils.functions import timeit, handle_kube_error

class ResourceList:
    def __init__(self, env: Optional[str] = None) -> None:
        self.env = env

    def parse_api_resources(self, raw_output: str):
        lines = raw_output.strip().splitlines()
        headers = lines[0].split()
        
        resources = []
        for line in lines[1:]:
            # 由于 VERBS 和 CATEGORIES 可能有空格，需要对齐字段
            parts = line.split(None, len(headers) - 1)  # split into exactly N parts
            resource = dict(zip(headers, parts))
            
            # 如果 VERBS 是逗号分隔的字符串，转成 list
            if "VERBS" in resource:
                resource["VERBS"] = resource["VERBS"].split(",")
            
            # NAMESPACED 是布尔值
            if "NAMESPACED" in resource:
                resource["NAMESPACED"] = resource["NAMESPACED"].lower() == "true"
            
            resources.append(resource)

        return resources


    @handle_kube_error
    @timeit
    def kubectl_get_api_resoucrs(
        self,
        api_group: Optional[str] = None,
        namespaced: Optional[bool] = None,
        output_type: Optional[str] = 'wide', 
    ) -> List[Dict[str, Any]]:
        """获取kubernetes可用api资源类型

        Args:
            api_group (Optional[str], optional): api资源类型
            namespaced (Optional[bool], optional): 是否支持namespace
            output_type (Optional[str], optional): 输出类型，支持wide

        Raises:
            RuntimeError: 当subprocess执行错误时抛出异常

        Returns:
            Dict: api资源类型
        """
        try:
            cmd = [
                "kubectl",
                "--kubeconfig", self.env,
                "api-resources",
                "-o", output_type
            ]
            
            if api_group:
                cmd += ["--api-group", api_group]
                
            if namespaced is not None:
                cmd += [f"--namespaced={str(namespaced).lower()}", ]  # true/false
                
            logger.debug(f"Exec cmd: {cmd}")
            
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = proc.communicate()

            if proc.returncode != 0:
                error_msg = stderr.decode().strip()
                logger.error(f"[kubectl_get_api_resoucrs] Error running: {error_msg}")
                raise RuntimeError(error_msg)

            return self.parse_api_resources(stdout.decode().strip())
            
        except subprocess.SubprocessError as e:
            logger.error(f"[kubectl_get_api_resoucrs] Subprocess error: {str(e)}")
            return [e]