import subprocess
import tempfile
import os
from typing import Optional, Any, List, Dict
from utils.logger import logger
from utils.functions import timeit, handle_kube_error

from template import (
    gen_ns_template,
    gen_deployment_template,
    gen_pod_template,
    gen_configmap_template,
    gen_sa_template,
    gen_service_template
)

class ResourceCreate:
    def __init__(self, env: Optional[str]) -> None:
        self.env = env

    def _exec_kubectl(self, cmd: list[str]) -> str:
        logger.debug(f"Exec cmd: {' '.join(cmd)}")
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()

        if proc.returncode != 0:
            error_msg = stderr.decode().strip()
            logger.error(f"[kubectl] Error: {error_msg}")
            raise RuntimeError(error_msg)

        return stdout.decode().strip()

    def kubectl_create(
        self,
        manifest: Optional[str] = None,
        filename: Optional[str] = None,
        namespace: Optional[str] = 'default',
    ) -> Any:
        """创建kubernetes资源

        Args:
            manifest (Optional[str], optional): 资源创建清单
            filename (Optional[str], optional): 资源清单文件
            namespace (Optional[str], optional): 资源所在的命名空间，默认为default

        Raises:
            ValueError: 当既定文件未传入时抛出异常

        Returns:
            Any: 资源对象或异常错误
        """
        try:
            cmd = [
                "kubectl",
                "--kubeconfig", self.env,
                "create",
            ]

            if filename:
                cmd += ["-f", filename]
                if namespace:
                    cmd += ["-n", namespace]
                return self._exec_kubectl(cmd)

            elif manifest:
                with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".yaml") as tmp:
                    tmp.write(manifest)
                    tmp_filename = tmp.name

                try:
                    cmd += ["-f", tmp_filename]
                    if namespace:
                        cmd += ["-n", namespace]
                    return self._exec_kubectl(cmd)
                finally:
                    os.remove(tmp_filename)

            else:
                raise ValueError("Either manifest or filename must be provided.")
        except Exception as e:
            logger.error(f"[kubectl_create] Error: {e}")
            return e

    @handle_kube_error
    @timeit
    def create_from_template(
        self,
        manifest: str,
        namespace: Optional[str] = 'default'
    ) -> str:
        """传入模板创建对应资源

        Args:
            manifest (str): 资源清单
            namespace (Optional[str], optional): 资源所在的命名空间，默认为default

        Returns:
            str: 模板创建后回调信息
        """
        try:
            return self.kubectl_create(manifest=manifest, namespace=namespace)
        except Exception as e:
            logger.error(f"[create_from_template] Error: {e}")
            return e

    @handle_kube_error
    @timeit
    def create_namespace(
        self,
        ns_name: str,
        labels: Optional[dict] = None,
        manifest: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> str:
        """创建namespace

        Args:
            ns_name (str): 命名空间名称
            labels (Optional[dict], optional): 标签
            manifest (Optional[str], optional): 资源清单列表
            filename (Optional[str], optional): 资源清单文件

        Returns:
            str: 创建回调信息
        """
        try:
            if manifest or filename:
                return self.kubectl_create(manifest=manifest, filename=filename)

            generated_manifest = gen_ns_template(ns_name, labels)
            return self.create_from_template(generated_manifest)
        except Exception as e:
            logger.error(f"[create_namespace] Error: {e}")
            return e

    def build_container(
        self,
        name: str,
        image: str,
        ports: Optional[List[int]] = None,
        image_pull_policy: str = "IfNotPresent"
    ) -> Dict[str, Any]:
        """构建容器字典

        Args:
            name (str): 容器名称
            image (str): 容器镜像
            ports (Optional[List[int]], optional): 容器端口，类型为Dict
            image_pull_policy (str, optional): 容器拉取策略，默认为IfNotPresent

        Returns:
            Dict[str, Any]: 容器字典
        """
        container = {
            "name": name,
            "image": image,
            "imagePullPolicy": image_pull_policy
        }
        if ports:
            container["ports"] = [{"containerPort": p} for p in ports]
        return container

    @handle_kube_error
    @timeit
    def create_pod(
        self,
        pod_name: str,
        labels: Optional[dict] = None,
        namespace: Optional[str] = 'default',
        containers: Optional[List[Dict[str, Any]]] = None,
        manifest: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> str:
        """创建pod

        Args:
            pod_name (str): pod名称
            labels (Optional[dict], optional): 标签
            containers (Optional[List[Dict[str, Any]]], optional): 容器列表
            manifest (Optional[str], optional): pod清单信息
            filename (Optional[str], optional): pod清单文件

        Returns:
            str: 创建pod回调信息
        """
        if manifest or filename:
            return self.kubectl_create(
                manifest=manifest,
                filename=filename,
                namespace=namespace
            )

        generated_manifest = gen_pod_template(
            name=pod_name,
            labels=labels,
            containers=containers
        )
        
        return self.create_from_template(
            manifest=generated_manifest,
            namespace=namespace
        )

    @handle_kube_error
    @timeit
    def create_deployment(
        self,
        name: str,
        replicas: int = 1,
        containers: Optional[List[Dict[str, Any]]] = None,
        labels: Optional[dict] = None,
        namespace: Optional[str] = "default",
        manifest: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> str:
        """创建deployment

        Args:
            name (str): deployment名称
            replicas (int, optional): 副本数量，默认为1
            containers (Optional[List[Dict[str, Any]]], optional): 容器列表
            labels (Optional[dict], optional): 标签
            namespace (Optional[str], optional): 资源所在的命名空间，默认为default
            manifest (Optional[str], optional): 资源清单
            filename (Optional[str], optional): 资源清单文件

        Returns:
            str: 创建deployment回调信息
        """
        try:
            if manifest or filename:
                return self.kubectl_create(
                    manifest=manifest,
                    filename=filename,
                    namespace=namespace
                )

            generated_manifest = gen_deployment_template(
                name=name,
                labels=labels,
                replicas=replicas,
                containers=containers
            )
            return self.create_from_template(
                generated_manifest,
                namespace=namespace
            )
        except Exception as e:
            logger.error(f"[create_deployment] Error: {e}")
            return e

    @handle_kube_error
    @timeit
    def create_configmap(
        self,
        map_name: Optional[str],
        data: Optional[List[Dict[str, Any]]] = None,
        namespace: Optional[str] = 'default',
        manifest: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> str:
        try:
            if manifest or filename:
                return self.kubectl_create(
                    manifest=manifest,
                    filename=filename,
                    namespace=namespace
                )
            generated_manifest = gen_configmap_template(
                name=map_name,
                data=data,
                namespace=namespace,
            )
            return self.create_from_template(
                generated_manifest,
                namespace=namespace
            )
        except Exception as e:
            logger.error(f"[create_configmap] Error: {e}")
            return e
       
    @handle_kube_error
    @timeit
    def create_serviceAccount(
        self,
        sa_name: str,
        labels: Optional[dict] = None,
        namespace: Optional[str] = 'default',
        manifest: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> str:
        """创建ServiceAccount

        Args:
            sa_name (str): ServiceAccount名称
            labels (Optional[dict], optional): 标签
            manifest (Optional[str], optional): 资源清单列表
            filename (Optional[str], optional): 资源清单文件

        Returns:
            str: 创建回调信息
        """
        try:
            if manifest or filename:
                return self.kubectl_create(
                    manifest=manifest,
                    filename=filename,
                    namespace=namespace
                )

            generated_manifest = gen_sa_template(
                sa_name=sa_name,
                labels=labels
            )
            return self.create_from_template(generated_manifest)
        except Exception as e:
            logger.error(f"[create_serviceAccount] Error: {e}")
            return e

    def run_kubectl_secret_dryrun(self, cmd: list) -> str:
        try:
            result = subprocess.run(
                cmd + ['--dry-run=client', '-o', 'yaml'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True
            )
            return result.stdout.decode()
        except subprocess.CalledProcessError as e:
            logger.error(f"[create_secret] kubectl error: {e.stderr.decode()}")
            raise

    @handle_kube_error
    @timeit
    def create_secret(
        self,
        secret_type: str,
        name: str,
        namespace: str = "default",
        data: Optional[Dict[str, str]] = None,
        cert: Optional[str] = None,
        key: Optional[str] = None,
        docker_username: Optional[str] = None,
        docker_password: Optional[str] = None,
        docker_server: Optional[str] = None,
    ) -> str:
        cmd = [
                "kubectl",
                "--kubeconfig", self.env,
                "create", "secret",
        ]

        if secret_type == "generic":
            cmd += ["generic", name]
            if data:
                for k, v in data.items():
                    cmd += ["--from-literal", f"{k}={v}"]

        elif secret_type == "tls":
            if not cert or not key:
                raise ValueError("TLS secret must include cert and key file paths")
            cmd += ["tls", name, "--cert", cert, "--key", key]

        elif secret_type == "docker-registry":
            if not docker_username or not docker_password or not docker_server:
                raise ValueError("Docker registry secret must include username, password, and server")
            cmd += [
                "docker-registry", name,
                "--docker-username", docker_username,
                "--docker-password", docker_password,
                "--docker-server", docker_server
            ]
        else:
            raise ValueError(f"Unsupported secret type: {secret_type}")

        logger.debug(f"Exec cmd: {cmd}")
        yaml_content = self.run_kubectl_secret_dryrun(cmd)

        with tempfile.NamedTemporaryFile('w+', suffix='.yaml', delete=False) as tmpfile:
            tmpfile.write(yaml_content)
            tmpfile_path = tmpfile.name

        create_cmd = ["kubectl", "create", "-f", tmpfile_path]
        
        if namespace:
            create_cmd += ["-n", namespace]

        try:
            output = subprocess.check_output(create_cmd).decode().strip()
            logger.info(f"[create_secret] Created secret: {output}")
            return output
        except Exception as e:
            logger.error(f"[create_secret] Failed: {e}")
            return e
        finally:
            os.remove(tmpfile_path)

    def build_port(
        self,
        name: str,
        protocol: str,
        port: Optional[int] = None,
        targetPort: Optional[int] = None,
        nodePort: Optional[int] = None,
    ) -> Dict[str, Any]:
        ports = {
            "name": name,
            "protocol": protocol,
            "port": port,
            "targetPort": targetPort,
        }
        if nodePort:
            ports["nodePort"] = nodePort
        return ports

    @handle_kube_error
    @timeit
    def create_service(
        self,
        service_name: str,
        labels: Optional[Dict[str, str]] = None,
        ports: Optional[List[Dict[str, Any]]] = None,
        selector: Optional[Dict[str, str]] = None,
        service_type: str = "ClusterIP",
        namespace: Optional[str] = 'default',
        manifest: Optional[str] = None,
        filename: Optional[str] = None,
    ) -> str:

        if manifest or filename:
            return self.kubectl_create(
                manifest=manifest,
                filename=filename,
                namespace=namespace
            )

        generated_manifest = gen_service_template(
            name=service_name,
            labels=labels,
            selector=selector,
            ports=ports,
            service_type=service_type
        )
        
        return self.create_from_template(
            manifest=generated_manifest,
            namespace=namespace
        )
