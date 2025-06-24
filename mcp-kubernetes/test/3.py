import subprocess
import signal
import os
import time
import threading

from typing import Optional, Dict
from utils.logger import logger
from utils.functions import timeit, handle_kube_error

class PortForwarder:
    def __init__(self, env: Optional[str]):
        self.env = env
        self.port_forward_processes: Dict[str, subprocess.Popen] = {}

    def _stream_reader(self, pipe, log_func):
        for line in iter(pipe.readline, ''):
            if line:
                log_func(line.strip())
        pipe.close()

    def _monitor_startup(self, proc, key, ready_event):
        """监控输出，等待 'Forwarding from' """
        for line in iter(proc.stdout.readline, ''):
            if "Forwarding from" in line:
                logger.debug(f"[{key}] Port-forward started: {line.strip()}")
                ready_event.set()
            logger.debug(f"[{key}][stdout] {line.strip()}")
        proc.stdout.close()

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
        key = f"{namespace}/{resource_type}/{resource_name}:{local_port}->{remote_port}"

        cmd = [
            "kubectl",
            "--kubeconfig", self.env,
            "-n", namespace,
            "port-forward",
            "--address", "0.0.0.0,::",
            f"{resource_type}/{resource_name}",
            f"{local_port}:{remote_port}"
        ]

        logger.debug(f"Exec cmd: {cmd}")
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                preexec_fn=os.setsid,
                text=True,
                bufsize=1
            )

            # 设置事件用于通知主线程
            ready_event = threading.Event()

            # 启动监控线程读取 stdout
            threading.Thread(target=self._monitor_startup, args=(proc, key, ready_event), daemon=True).start()

            # stderr 日志也异步读，防止卡住
            threading.Thread(target=self._stream_reader, args=(proc.stderr, logger.error), daemon=True).start()

            # 等待最多 5 秒
            if ready_event.wait(timeout=5):
                self.port_forward_processes[key] = proc
                logger.info(f"✅ Port-forward started for {key}, PID {proc.pid}")
                return str(proc.pid)
            else:
                os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
                logger.error("⏰ Timeout waiting for port-forward to start")
                return "❌ Timeout: port-forward did not confirm startup"

        except Exception as e:
            logger.error(f"❌ Exception while starting port-forward: {e}")
            return f"❌ Failed to start port-forward: {str(e)}"

    @timeit
    def stop_port_forward(self, proc_id: int) -> str:
        try:
            os.killpg(os.getpgid(proc_id), signal.SIGTERM)
            logger.info(f"🛑 Stopped port-forward (PID {proc_id})")
            return f"✅ Stopped port-forward (PID {proc_id})"
        except Exception as e:
            logger.error(f"❌ Failed to stop port-forward: {e}")
            return f"❌ Failed to stop: {str(e)}"
