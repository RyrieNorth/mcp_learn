import os
import re
import tty
import time
import termios
import libvirt
import atexit
import socket
from utils.connect import LibvirtConnector
from utils.details import VM_STATES
from utils.logger import logger
from typing import Any, Optional

ESCAPE_KEY = b'\x1d'  # Ctrl + ]

def reset_terminal():
    """重置终端属性为原始状态
    """
    if hasattr(reset_terminal, "attrs"):
        termios.tcsetattr(0, termios.TCSADRAIN, reset_terminal.attrs)
        
        
def stream_callback(stream: socket.socket, events: int, context: dict) -> None:
    """流传输回调函数，用于接收并输出流中的数据

    Args:
        stream (socket): 数据流对象
        events (int): 触发回调的事件类型
        context (dict): 上下文字典，用于共享状态
    """
    try:
        data = stream.recv(1024)
        os.write(1, data)
    except Exception:
        context["run"] = False
        

def stdin_callback(watch: Any, fd: int, events: int, context: dict) -> None:
    """标准输入回调函数，用于接收并输出流中的数据

    Args:
        watch (Any): 观察者对象或事件注册的引用（通常由事件循环库传入，如 GLib 的 IO watch）
        fd (int): 文件描述符
        events (int): 触发回调的事件类型
        context (_type_): 上下文字典，用于共享状态
    """
    try:
        data = os.read(fd, 1024)
        if data.startswith(ESCAPE_KEY):
            context["run"] = False
        else:
            context["stream"].send(data)
    except Exception:
        context["run"] = False


class LibvirtConsole:
    def __init__(self, vm_id=None, vm_name=None, vm_uuid=None):
        """初始化console连接

        Args:
            vm_id (_type_, optional): 虚拟机id
            vm_name (_type_, optional): 虚拟机名称
            vm_uuid (_type_, optional): 虚拟机uuid
        """
        self.vm_id = vm_id
        self.vm_name = vm_name
        self.vm_uuid = vm_uuid


    def connect(self, vm_id: Optional[int] = None, vm_name: Optional[str] = None, vm_uuid: Optional[str] = None) -> Any:
        """
        连接到虚拟机控制台，通过 vm_id、vm_name 或 vm_uuid 定位虚拟机。

        Args:
            vm_id (Optional[int]): 虚拟机的 ID
            vm_name (Optional[str]): 虚拟机名称
            vm_uuid (Optional[str]): 虚拟机的 UUID

        Returns:
            Any: None 或异常退出
        """        
        # 兼容单一位置参数
        if vm_id and (vm_name or vm_uuid):
            raise ValueError("Please provide only one args vm_id / vm_name / vm_uuid")
        if vm_name is None and vm_uuid is None and isinstance(vm_id, str):
            vm_name, vm_id = vm_id, None

        if isinstance(vm_id, str) and '-' in vm_id:
            vm_uuid, vm_id = vm_id, None

        if not (vm_id or vm_name or vm_uuid):
            raise ValueError("Either vm_id, vm_name or vm_uuid must be provided")

        # 保存原始终端设置并切换为原始模式
        reset_terminal.attrs = termios.tcgetattr(0)
        atexit.register(reset_terminal)

        try:
            libvirt.registerErrorHandler(lambda *_: None, None)
            libvirt.virEventRegisterDefaultImpl()

            conn = LibvirtConnector().connect()
            if not conn:
                raise RuntimeError("Failed to get libvirt connection.")

            tty.setraw(0)

            if vm_id:
                domain = conn.lookupByID(vm_id)
            elif vm_name:
                domain = conn.lookupByName(vm_name)
            elif vm_uuid:
                domain = conn.lookupByUUIDString(vm_uuid)

            state, _ = domain.state(0)
            if state not in (libvirt.VIR_DOMAIN_RUNNING, libvirt.VIR_DOMAIN_PAUSED):
                raise RuntimeError(f"VM {domain.name()} cannot be connected, now state: {VM_STATES[state]}")

            stream = conn.newStream(libvirt.VIR_STREAM_NONBLOCK)
            domain.openConsole(None, stream, 0)

            logger.info("Escape character is ^]\r")
            print("Escape character is ^]\r")
            context = {"run": True, "stream": stream}
            stream.eventAddCallback(libvirt.VIR_STREAM_EVENT_READABLE, stream_callback, context)
            libvirt.virEventAddHandle(0, libvirt.VIR_EVENT_HANDLE_READABLE, stdin_callback, context)

            while context["run"]:
                libvirt.virEventRunDefaultImpl()

            stream.finish()

        except Exception as e:
            logger.error(f"Connection failed: {e}")
            raise

        finally:
            reset_terminal()
            conn.close()
            print("\r")
            logger.info("Console exit")
            print("Exit.")
