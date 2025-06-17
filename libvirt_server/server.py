import httpx
import json
import subprocess
import sys

from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Any, Optional, Tuple, Union, Literal

from utils.logger import logger
from utils.libvirt_server import LibvirtServer


# Create libvirt mcp server
host = "0.0.0.0"
port = 8000
mcp = FastMCP("Libvirt Server", host=host, port=port, log_level="INFO", log_requests=True)
logger.info(f"MCP '{mcp.name}' initialized on {host}:{port}")

# Create libvirt server connector object
server = LibvirtServer()

# Register mcp tools
@mcp.tool()
def fetch_time(timezone: str = "Asia/Shanghai") -> str:
    """
    获取指定时区的当前时间信息。

    Args:
        timezone (str): 时区名称，例如 "Asia/Shanghai"

    Returns:
        str: 包含当前时间信息的 JSON 字符串
    """
    client = httpx.Client()
    response = client.get(
        url="https://timeapi.io/api/time/current/zone",
        params={"timeZone": timezone}
    )
    response.raise_for_status()
    return json.dumps(response.json(), ensure_ascii=False)

@mcp.tool()
def console_exec(
    vm_name: Optional[str], 
    username: Optional[str],
    password: Optional[str],
    command: Optional[str]
) -> str:
    """
    通过 expect 脚本连接控制台并执行命令。

    Args:
        vm_name (str): 虚拟机名称
        username (str): 登录用户名
        password (str): 登录密码
        command (str): 要执行的命令

    Returns:
        str: 命令输出
    """
    try:
        result = subprocess.run(
            ["expect", "console_exec.expect", vm_name, username, password, command],
            capture_output=True,
            timeout=20
        )
        if result.returncode != 0:
            return f"[ERROR] Failed to execute: {result.stderr.decode(errors='ignore')}"
        return result.stdout.decode(errors="ignore").strip()
    except Exception as e:
        return f"[EXCEPTION] {e}"

@mcp.tool()
def get_virtual_host_info(info_type: str = "full") -> Dict:
    """
    获取虚拟化宿主机信息，支持主机名、CPU、NUMA、完整信息等。

    Args:
        info_type (str): 信息类型，支持以下取值：
        - "hostname": 主机名
        - "cpu": CPU 信息
        - "numa": NUMA 和内存信息
        - "full": 完整信息

    Returns:
        Dict: 请求的宿主机信息
    """
    if info_type == "hostname":
        return server.host.get_hostname()
    elif info_type == "cpu":
        return server.host.get_host_cpu_info()
    elif info_type == "numa":
        return server.host.get_numa_memory_info()
    elif info_type == "full":
        return server.host.get_host_full_info()
    else:
        raise ValueError(f"Unsupported info_type: {info_type}")

@mcp.tool()
def virtual_network_ops(
    action: Literal["list", "get", "create", "delete"],
    net_name: Optional[str] = None,
    net_uuid: Optional[str] = None,
    br_name: Optional[str] = None,
    gateway: Optional[str] = None,
    netmask: Optional[str] = None,
    dhcp_start: Optional[str] = None,
    dhcp_end: Optional[str] = None
) -> Union[Dict, List[str], bool]:
    """
    统一虚拟网络操作工具，支持查询、创建、删除虚拟网络。

    Args:
        action (str): 操作类型，支持 "list", "get", "create", "delete"
        net_name/net_uuid: 用于查询或删除网络
        br_name/gateway/netmask/dhcp_start/dhcp_end: 创建网络所需参数

    Returns:
        Union[Dict, List[str], bool]: 网络列表、详情或操作结果
    """
    if action == "list":
        return server.net.list_networks()
    elif action == "get":
        return server.net.get_network_info(net_name=net_name, net_uuid=net_uuid)
    elif action == "create":
        if not all([net_name, br_name, gateway, netmask, dhcp_start, dhcp_end]):
            raise ValueError("Creating network requires all parameters.")
        return server.net.create_network(
            net_name=net_name,
            br_name=br_name,
            gateway=gateway,
            netmask=netmask,
            dhcp_start=dhcp_start,
            dhcp_end=dhcp_end
        )
    elif action == "delete":
        return server.net.delete_network(net_name=net_name, net_uuid=net_uuid)
    else:
        raise ValueError(f"Unsupported action: {action}")

@mcp.tool()
def bridge_ops(
    action: Literal["create", "delete", "list", "list_interfaces", "add_interface", "remove_interface"],
    bridge_name: Optional[str] = None,
    interfaces: Optional[List[str]] = None
) -> Union[bool, Dict]:
    """
    虚拟网桥操作工具，支持创建、删除、列出接口、绑定/解绑接口等功能。

    Args:
        action (str): 操作类型：
            - "create": 创建网桥
            - "delete": 删除网桥
            - "list": 列出系统中所有网卡接口
            - "list_interfaces": 列出指定网桥下的接口
            - "add_interface": 绑定接口到网桥
            - "remove_interface": 从网桥解绑接口
        bridge_name (Optional[str]): 网桥名称（某些操作必填）
        interfaces (Optional[List[str]]): 要操作的接口列表（add/remove 时必填）

    Returns:
        Union[bool, Dict]: 操作结果或信息字典
    """
    if action == "create":
        if not bridge_name:
            raise ValueError("bridge_name is required for 'create'")
        return server.br.create(bridge_name=bridge_name)

    elif action == "delete":
        if not bridge_name:
            raise ValueError("bridge_name is required for 'delete'")
        return server.br.delete(bridge_name=bridge_name)

    elif action == "list":
        return server.br.list_interface()

    elif action == "list_interfaces":
        if not bridge_name:
            raise ValueError("bridge_name is required for 'list_interfaces'")
        return server.br.list_br_interface(bridge_name=bridge_name)

    elif action == "add_interface":
        if not bridge_name or not interfaces:
            raise ValueError("bridge_name and interfaces are required for 'add_interface'")
        return server.br.interface_operation(bridge_name, interfaces, action="add")

    elif action == "remove_interface":
        if not bridge_name or not interfaces:
            raise ValueError("bridge_name and interfaces are required for 'remove_interface'")
        return server.br.interface_operation(bridge_name, interfaces, action="delete")

    else:
        raise ValueError(f"Unsupported action '{action}'")

@mcp.tool()
def storage_pool_ops(
    action: Literal["create", "delete", "list", "info"],
    pool_type: Optional[str] = None,
    pool_name: Optional[str] = None,
    pool_path: Optional[str] = None,
    pool_uuid: Optional[str] = None
) -> Union[bool, List[Dict], Dict]:
    """
    存储池操作工具，支持创建、删除、列出、查看详情。

    Args:
        action (str): 操作类型：
            - "create": 创建存储池
            - "delete": 删除存储池
            - "list": 获取所有存储池信息
            - "info": 获取指定存储池详情
        pool_type (str): 存储池类型（仅创建时必填）
        pool_name (str): 存储池名称
        pool_path (str): 存储池挂载路径（创建时必填）
        pool_uuid (str): 存储池 UUID（info/delete 时可选）

    Returns:
        Union[bool, List[Dict], Dict]: 操作成功与否或查询结果
    """
    if action == "create":
        if not all([pool_type, pool_name, pool_path]):
            raise ValueError("Creating storage pool requires 'pool_type', 'pool_name', and 'pool_path'")
        return server.pool.create_pool(
            pool_type=pool_type,
            pool_name=pool_name,
            pool_path=pool_path,
        )

    elif action == "delete":
        if not pool_name and not pool_uuid:
            raise ValueError("Deleting storage pool requires 'pool_name' or 'pool_uuid'")
        return server.pool.delete_pool(
            pool_name=pool_name,
            pool_uuid=pool_uuid
        )

    elif action == "list":
        return server.pool.list_pools()

    elif action == "info":
        if not pool_name and not pool_uuid:
            raise ValueError("Info requires 'pool_name' or 'pool_uuid'")
        return server.pool.pool_info(
            pool_name=pool_name,
            pool_uuid=pool_uuid
        )

    else:
        raise ValueError(f"Unsupported action: {action}")

@mcp.tool()
def get_virtual_machine_info(
    query_type: str,
    vm_name: Optional[str] = None,
    vm_uuid: Optional[str] = None,
    device_types: Optional[List[str]] = None,
    disk_path: Optional[str] = None
) -> Union[Dict, List[Tuple[int, str]]]:
    """
    获取虚拟机相关信息（支持列表、详细信息、磁盘信息）

    Args:
        query_type (str): 查询类型，可选项:
            - "list": 获取所有虚拟机
            - "info": 获取指定虚拟机的核心和设备信息
            - "disk": 获取指定磁盘的 qemu-img 信息
        vm_name (Optional[str]): 虚拟机名称（用于 info 查询）
        vm_uuid (Optional[str]): 虚拟机 UUID（用于 info 查询）
        device_types (Optional[List[str]]): 查询的设备类型（用于 info 查询）
        disk_path (Optional[str]): 磁盘路径（用于 disk 查询）

    Returns:
        Union[Dict, List[Tuple[int, str]]]: 查询结果
    """
    if query_type == "list":
        return server.vm.list_domains()
    elif query_type == "info":
        if not vm_name and not vm_uuid:
            raise ValueError("vm_name 或 vm_uuid 至少提供一个")
        return server.vm.domain_info(
            domain_name=vm_name,
            domain_uuid=vm_uuid,
            device_types=device_types
        )
    elif query_type == "disk":
        if not disk_path:
            raise ValueError("disk_path 是必需的")
        return server.vm.parse_qemu_img_info(disk_path=disk_path)
    else:
        raise ValueError("query_type 仅支持 'list', 'info', 'disk'")

@mcp.tool()
def manage_virtual_machine(
    action: str,
    domain_name: Optional[str] = None,
    domain_uuid: Optional[str] = None,
    state: Optional[str] = None,
    memory: Optional[int] = None,
    vcpus: Optional[int] = None,
    save_path: Optional[str] = None,
    name: Optional[str] = None,
    ram: Optional[int] = None,
    net_name: Optional[str] = None,
    os_arch: Optional[str] = "x86_64",
    emulator: Optional[str] = "/usr/libexec/qemu-kvm",
    boot_disk: Optional[str] = None,
    cdrom: Optional[str] = '',
    running: Optional[bool] = False,
) -> bool:
    """
    管理虚拟机生命周期和配置

    Args:
        action (str): 操作类型，可选项:
            - 生命周期管理: "start", "shutdown", "destroy", "pause", "resume", "reboot", "reset"
            - 特殊指令: "ctrl_alt_del", "undefine", "delete"
            - 自动启动: "set_autostart"
            - 配置变更: "set_memory", "set_vcpu"
            - 快照休眠: "save", "restore"
            - 虚拟机创建: "create"
        domain_name / domain_uuid: 指定虚拟机标识
        其他参数：根据具体action类型选择性填写

    Returns:
        bool: 操作是否成功
    """
    if action == "start":
        return server.vm.start(domain_name=domain_name, domain_uuid=domain_uuid)
    elif action == "shutdown":
        return server.vm.shutdown(domain_name=domain_name, domain_uuid=domain_uuid)
    elif action == "destroy":
        return server.vm.destroy(domain_name=domain_name, domain_uuid=domain_uuid)
    elif action == "pause":
        return server.vm.pause(domain_name=domain_name, domain_uuid=domain_uuid)
    elif action == "resume":
        return server.vm.resume(domain_name=domain_name, domain_uuid=domain_uuid)
    elif action == "reboot":
        return server.vm.reboot(domain_name=domain_name, domain_uuid=domain_uuid)
    elif action == "reset":
        return server.vm.reset(domain_name=domain_name, domain_uuid=domain_uuid)
    elif action == "ctrl_alt_del":
        return server.vm.send_ctrl_alt_del(domain_name=domain_name, domain_uuid=domain_uuid)
    elif action == "undefine":
        return server.vm.undefine(domain_name=domain_name, domain_uuid=domain_uuid)
    elif action == "delete":
        return server.vm.delete(domain_name=domain_name, domain_uuid=domain_uuid)
    elif action == "set_autostart":
        return server.vm.set_auto_start(domain_name=domain_name, domain_uuid=domain_uuid, state=state)
    elif action == "set_memory":
        return server.vm.set_memory(domain_name=domain_name, domain_uuid=domain_uuid, memory=memory)
    elif action == "set_vcpu":
        return server.vm.set_vcpu(domain_name=domain_name, domain_uuid=domain_uuid, vcpus=vcpus)
    elif action == "save":
        return server.vm.save(domain_name=domain_name, domain_uuid=domain_uuid, save_path=save_path)
    elif action == "restore":
        return server.vm.restore(save_path=save_path)
    elif action == "create":
        return server.vm.create(
            name=name,
            ram=ram,
            vcpu=vcpus,
            net_name=net_name,
            os_arch=os_arch,
            emulator=emulator,
            boot_disk=boot_disk,
            cdrom=cdrom,
            running=running
        )
    else:
        raise ValueError(f"不支持的操作类型: {action}")

@mcp.tool()
def get_vm_info(
    method: Literal[
        "state", "cputime", "ipaddrs", 
        "netstats", "diskstats", "hostname", 
        "full_stats"
    ],
    domain_name: Optional[str] = None,
    domain_uuid: Optional[str] = None,
    interval: Optional[float] = 1.0,
    to_mib: Optional[bool] = False,
) -> Dict:
    """
    获取虚拟机相关信息，支持多种信息类型，按 method 参数指定。

    Args:
        method (str): 
        - "state"
        - "cputime"
        - "ipaddrs"
        - "netstats"
        - "diskstats"
        - "hostname"
        - "full_stats"
        domain_name (str): 虚拟机名称
        domain_uuid (str): 虚拟机 UUID
        interval (float): 仅对 cputime 有效的采样时间
        to_mib (bool): 是否以 MiB 输出（适用于 netstats、diskstats、full_stats）

    Returns:
        Dict: 虚拟机指定信息
    """
    if method == "state":
        return server.vm.domain_state(domain_name=domain_name, domain_uuid=domain_uuid)
    elif method == "cputime":
        return server.vm.domain_cputime(domain_name=domain_name, domain_uuid=domain_uuid, interval=interval)
    elif method == "ipaddrs":
        return server.vm.domain_ipaddrs(domain_name=domain_name, domain_uuid=domain_uuid)
    elif method == "netstats":
        return server.vm.domain_netstats(domain_name=domain_name, domain_uuid=domain_uuid, to_mib=to_mib)
    elif method == "diskstats":
        return server.vm.domain_diskstats(domain_name=domain_name, domain_uuid=domain_uuid, to_mib=to_mib)
    elif method == "hostname":
        return server.vm.domain_hostname(domain_name=domain_name, domain_uuid=domain_uuid)
    elif method == "full_stats":
        return server.vm.domain_full_stats(domain_name=domain_name, domain_uuid=domain_uuid, to_mib=to_mib)
    else:
        raise ValueError(f"Unsupported VM info method: {method}")

@mcp.tool()
def manage_volume(
    action: str,
    storage_pool: Optional[str] = None,
    vol_name: Optional[str] = None,
    vol_size: Optional[int] = None,
    vol_path: Optional[str] = None,
    src_vol_name: Optional[str] = None,
    clone_vol_name: Optional[str] = None,
    file_path: Optional[str] = None,
    local_path: Optional[str] = None,
) -> Union[bool, List[Dict[str, Any]]]:
    """
    存储卷管理函数，统一处理 list/create/clone/delete/download/upload 等操作。

    Args:
        action (str): 操作类型，可选：
            - list
            - create
            - clone
            - delete
            - download
            - upload
        其余参数根据 action 不同而有所需要。

    Returns:
        Union[bool, List[Dict]]: 根据操作返回布尔值或卷列表
    """
    if action == "list":
        return server.vol.list_volumes(storage_pool=storage_pool)
    elif action == "create":
        return server.vol.create(
            storage_pool=storage_pool,
            vol_name=vol_name,
            vol_size=vol_size,
            vol_path=vol_path
        )
    elif action == "clone":
        return server.vol.clone(
            storage_pool=storage_pool,
            src_vol_name=src_vol_name,
            clone_vol_name=clone_vol_name
        )
    elif action == "delete":
        return server.vol.delete(
            storage_pool=storage_pool,
            vol_name=vol_name
        )
    elif action == "download":
        return server.vol.transfer(
            pool_name=storage_pool,
            vol_name=vol_name,
            file_path=file_path,
            action="download"
        )
    elif action == "upload":
        return server.vol.create_and_upload(
            pool_name=storage_pool,
            vol_name=vol_name,
            vol_path=vol_path,
            local_path=local_path
        )
    else:
        raise ValueError(f"Unsupported volume action: {action}")


tool_count = 0
for tool in mcp._tool_manager.list_tools():
    logger.info(f"Registered tool: {tool.name}")
    tool_count +=1

logger.info(f"Total registered tools: {tool_count}")


if __name__ == "__main__":
    try:
        mcp.run(transport="streamable-http")
    except KeyboardInterrupt:
        logger.info(f"Closing Libvirt Server...")
        sys.exit(0)
    except EOFError:
        logger.info(f"Closing Libvirt Server...")
        sys.exit(0)
