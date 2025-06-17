import libvirt
from utils.logger import logger
from utils.functions import timeit, run_cmd
from typing import List, Dict, Optional


class NetManager:
    def __init__(self, conn: libvirt.virConnect):
        self.conn = conn

    @timeit
    def list_networks(self) -> List:
        """列出所有的libvirt网络设备

        Returns:
            List: 返回一个列表
            - [{'net_name': 'default'}]
        """
        result: List = []
        try:
            nets = self.conn.listNetworks()
            for net in nets:
                result.append({"net_name": net})
                
        except libvirt.libvirtError as e:
            logger.error(f"Failed to list networks: {e}")
            return []
        
        return result

    @timeit
    def get_network_info(self, net_name: Optional[str] = None, net_uuid: Optional[str] = None) -> Optional[Dict]:
        """获取网络的详细信息，可通过名称或 UUID 查询

        Args:
            net_name (str, optional): 虚拟网络名称
            net_uuid (str, optional): 虚拟网络uuid

        Returns:
            Dict: 返回一个虚拟网络字典
            - net_name (str): 虚拟网络名称
            - net_uuid (str): 虚拟网络uuid
            - net_bridge (str): 虚拟网络网桥
            - autostart (bool): 是否开机自启
            - is_active (bool): 是否运行
            - is_persistent (bool): 是否持久化
        """
        if net_name and (net_uuid is not None):
            raise ValueError("Please provide only one of net_name or net_uuid")

        if net_uuid is None and net_name is not None:
            if '-' in net_name:
                net_uuid, net_name = net_name, None

        if not net_name and not net_uuid:
            raise ValueError("Either net_name or net_uuid must be provided")
        
        try:
            if net_name:
                network = self.conn.networkLookupByName(net_name)
            elif net_uuid:
                network = self.conn.networkLookupByUUIDString(net_uuid)

            return {
                "net_name": network.name(),
                "net_uuid": network.UUIDString(),
                "net_bridge": network.bridgeName(),
                "autostart": bool(network.autostart()),
                "is_active": bool(network.isActive()),
                "is_persistent": bool(network.isPersistent())
            }

        except (libvirt.libvirtError, ValueError) as e:
            logger.error(f"Failed to get network info: {e}")
            return None

    @timeit
    def create_network(self, net_name: str, br_name: str, gateway: str, netmask: str, dhcp_start: str, dhcp_end: str) -> bool:
        """创建虚拟网络

        Args:
            net_name (str): 虚拟网络名称
            br_name (str): 虚拟网桥名称
            gateway (str): 虚拟网桥ip地址
            netmask (str): 虚拟网桥ip段掩码
            dhcp_start (str): 虚拟网络dhcp起始ip
            dhcp_end (str): 虚拟网络dhcp休止ip

        Returns:
            bool: True为创建成功，反之创建失败
        """

        xml = f"""
        <network>
            <name>{net_name}</name>
            <bridge name="{br_name}" />
            <forward mode="nat" />
            <ip address="{gateway}" netmask="{netmask}">
                <dhcp>
                    <range start="{dhcp_start}" end="{dhcp_end}" />
                </dhcp>
            </ip>
        </network>
        """
        
        try:
            network = self.conn.networkDefineXML(xml)
            network.create()
            network.setAutostart(1)
            logger.info(f"Create virtual network {net_name} success")
            return True
        except libvirt.libvirtError as e:
            logger.error(f"Failed to create virtual network {net_name}: {e}")
            return False

    @timeit
    def delete_network(self, net_name: str = None, net_uuid: str = None) -> bool:
        """删除虚拟网络

        Args:
            net_name (str): 虚拟网络名称
            net_uuid (str): 虚拟网络uuid

        Returns:
            bool: True为创建成功，反之创建失败
        """
        if net_name and (net_uuid is not None):
            raise ValueError("Please provide only one of net_name or net_uuid")

        if net_uuid is None and net_name is not None:
            if '-' in net_name:
                net_uuid, net_name = net_name, None

        if not net_name and not net_uuid:
            raise ValueError("Either net_name or net_uuid must be provided")

        try:
            if net_name:
                network = self.conn.networkLookupByName(net_name)
            elif net_uuid:
                network = self.conn.networkLookupByUUIDString(net_uuid)
            
            network.destroy()
            network.undefine()
            logger.info(f"Delete virtual network {net_name} success")
            return True
        except libvirt.libvirtError as e:
            logger.error(f"Failed to delete virtual network {net_name}: {e}")
            return False


class BridgeManager:
    """用于管理网桥
    """
    def __init__(self, run_cmd_func):
        """
        初始化 BridgeManager
        :param run_cmd_func: 外部传入的命令执行函数，返回 (status, stdout, stderr)
        """
        self.run_cmd = run_cmd_func
        self._check_brctl_cmd()

    def _check_brctl_cmd(self):
        """检查 brctl 命令是否安装"""
        status, _, _ = self.run_cmd(cmd="command -v brctl")
        if status != 0:
            logger.error("Command `brctl` not found. Please install bridge-utils.")
            raise EnvironmentError("Missing brctl command")

    def _bridge_exists(self, bridge_name: str) -> bool:
        """判断桥接是否存在"""
        status, _, _ = self.run_cmd(f"brctl show | grep -w {bridge_name}")
        return status == 0

    @timeit
    def create(self, bridge_name: str) -> bool:
        """
        创建 bridge
        :param bridge_name: 桥接名称
        """
        if self._bridge_exists(bridge_name):
            logger.error(f"Bridge '{bridge_name}' already exists.")
            return False

        status, _, _ = self.run_cmd(f"brctl addbr {bridge_name}")
        if status != 0:
            logger.error(f"Failed to create bridge '{bridge_name}'")
            return False

        status, _, err = self.run_cmd(f"ip link set {bridge_name} up")
        if status != 0:
            logger.error(f"Failed to bring bridge '{bridge_name}' up: {err.strip()}")
            return False

        logger.info(f"Bridge '{bridge_name}' created successfully.")
        return True

    @timeit
    def delete(self, bridge_name: str) -> bool:
        """
        删除 bridge（会先解绑所有接口）
        :param bridge_name: 桥接名称
        """
        if not self._bridge_exists(bridge_name):
            logger.error(f"Bridge '{bridge_name}' not found.")
            return False

        self.run_cmd(f"ip link set {bridge_name} down")

        status, _, err = self.run_cmd(f"brctl delbr {bridge_name}")
        if status != 0:
            logger.error(f"Failed to delete bridge '{bridge_name}': {err.strip()}")
            return False

        logger.info(f"Bridge '{bridge_name}' deleted successfully.")
        return True

    @timeit
    def list_interface(self) -> Dict:
        """列出所有网络接口

        Returns:
            Dict: 返回一个字典
            - {'interfaces': ['enp7s0', 'wlan1', 'wlp8s0']}
        """
        cmd = "cat /proc/net/dev | grep -Ev 'lo|face|Inter|br|qvo|qvb|qbr|ovs|docker|vnet|veth|tap' | sort | awk '{i++;{print $1}}' | tr -d ':'"
        status, stdout, stderr = run_cmd(cmd=cmd)
        if status != 0:
            logger.error(f"Failed to get host network interfaces : {stderr.strip()}")
            return
        return {
            "interfaces": stdout.strip().split('\n') 
        }

    @timeit
    def list_br_interface(self, bridge_name: str) -> Dict:
        """列出指定网桥网络接口

        Returns:
            Dict: 返回一个字典
            - {'interfaces': ['enp7s0', 'wlan1', 'wlp8s0']}
        """
        if self._bridge_exists(bridge_name):        
            cmd = f"brctl show {bridge_name} | awk 'NR>1 {{if ($4 != \"\") print $4; else print $1}}'"
            status, stdout, stderr = run_cmd(cmd=cmd)
            if status != 0:
                logger.error(f"Failed to get host network interfaces : {stderr.strip()}")
                return
            if stdout.strip() == bridge_name:
                logger.warning(f"Not ifaces in {bridge_name}")
                return False
            
            return {
                "interfaces": stdout.strip().split('\n') 
            }
        else:
            logger.warning(f"Bridge {bridge_name} not exists")
            return False

    @timeit
    def interface_operation(self, bridge_name: str, interfaces: List[str], action: str = "add") -> bool:
        """
        添加或删除接口到 bridge 中
        :param bridge_name: 桥接名称
        :param interfaces: 接口列表
        :param action: 操作类型 'add' 或 'del'
        """
        assert action in ["add", "del"], "Action must be 'add' or 'del'"

        if not self._bridge_exists(bridge_name):
            logger.error(f"Bridge '{bridge_name}' not found.")
            return False

        for iface in interfaces:
            cmd = f"brctl {action}if {bridge_name} {iface}"
            status, _, err = self.run_cmd(cmd)
            if status != 0:
                logger.error(f"{action.capitalize()} {iface} {'to' if action == 'add' else 'from'} {bridge_name} failed: {err.strip()}")
                return False

        logger.info(f"{'Bind' if action == 'add' else 'Unbind'} interfaces {interfaces} {'to' if action == 'add' else 'from'} bridge '{bridge_name}' successfully.")
        return True

    @timeit
    def bind(self, bridge_name: str, interfaces: List[str]) -> bool:
        """绑定接口"""
        return self.interface_operation(bridge_name, interfaces, action="add")

    @timeit
    def unbind(self, bridge_name: str, interfaces: List[str]) -> bool:
        """解绑接口"""
        return self.interface_operation(bridge_name, interfaces, action="del")
