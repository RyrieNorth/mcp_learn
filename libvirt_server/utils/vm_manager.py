import libvirt
import time
import subprocess
import yaml
import re
from utils.logger import logger
from utils.details import VM_STATES, NET_STATES, BLOCK_STATES
from utils.env_utils import get_env_var
from utils.functions import timeit, handle_libvirt_error
from utils.logger import logger
from typing import Dict, Optional, List, Tuple
from lxml import etree

def bytes_to_mib(byte_value: int) -> float:
    """字节换算，Byte to GiB

    Args:
        byte_value (int): 字节值

    Returns:
        float: 返回浮点数，取小数点前两位
    """
    return round(byte_value / (1024 ** 2), 2)

class VMManager:
    def __init__(self, conn: libvirt.virConnect):
        self.conn = conn

    @timeit
    def parse_qemu_img_info(self, disk_path: str) -> Dict:
        """远程调用 qemu-img 获取磁盘详细信息

        Args:
            disk_path (str): qemu磁盘路径

        Raises:
            RuntimeError: 若subprocess执行返回stderr，则弹出运行异常

        Returns:
            Dict: 磁盘详细信息字典
        """
        try:
            cmd = f"ssh root@{get_env_var("LIBVIRT_HOST")} command -v qemu-img"
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = proc.communicate()
            if not stdout:
                raise RuntimeError("Command qemu-img not found, please install it and try again later")
            
            cmd = f"ssh root@{get_env_var("LIBVIRT_HOST")} qemu-img info '{disk_path}'"
            proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = proc.communicate()
            if stderr:
                raise RuntimeError(f"{stderr.decode().strip()}")
            
        except Exception as e:
            logger.warning(e)
            return {}

        output, snapshots, columns = [], False, None
        for line in stdout.decode().splitlines():
            if line.startswith('Snapshot list:'):
                snapshots = True
                continue
            elif snapshots:
                if line.startswith('ID'):
                    line = line.replace('VM SIZE', 'VMSIZE').replace('VM CLOCK', 'TIME VMCLOCK')
                    columns = [c.lower() for c in re.split(r'\s+', line)]
                    output.append("snapshots:")
                    continue
                fields = re.split(r'\s+', line)
                for i, field in enumerate(fields):
                    sep = '-' if i == 0 else ' '
                    output.append(f"{sep} {columns[i]}: \"{field}\"")
            else:
                output.append(line)

        try:
            return yaml.safe_load('\n'.join(output))
        except yaml.YAMLError:
            return {}

    @timeit
    def extract_device_info(self, domain: libvirt.virDomain, include_types: List[str]) -> List[Dict[str, str]]:
        """仅提取指定类型的设备信息（如 disk、interface 等）

        Args:
            domain (libvirt.virDomain): 虚拟机对象实例
            include_types (List[str]): 指定设备类型

        Returns:
            List[Dict[str, str]]: 设备信息序列化字典
        """
        result = []

        try:
            root = etree.fromstring(domain.XMLDesc(0).encode())
            for d in root.xpath("/domain/devices/*"):
                dtype = d.tag
                if dtype not in include_types:
                    continue

                entry = {"type": dtype}

                if dtype == "disk":
                    entry["device_type"] = d.get("device", "")
                    source, target = d.find("source"), d.find("target")
                    entry["target"] = target.get("dev", "") if target is not None else ""

                    source_val = next((source.get(k) for k in ("file", "dev", "name") if source is not None and source.get(k)), "")
                    entry["source"] = source_val

                    # 可选添加详细磁盘信息
                    if entry["source"]:
                        entry.update(self.parse_qemu_img_info(entry["source"]))

                elif dtype == "interface":
                    entry["device_type"] = d.get("type", "")
                    source = d.find("source")
                    target = d.find("target")
                    mac = d.find("mac")
                    if source is not None:
                        entry["source"] = next(iter(source.attrib.values()), "")
                    if target is not None:
                        entry["target"] = next(iter(target.attrib.values()), "")
                    if mac is not None:
                        entry["mac_address"] = mac.get("address", "")

                elif dtype == "graphics":
                    entry.update({
                        "device_type": d.get("type", ""),
                        "port": d.get("port", ""),
                    })
                    listen = d.find("listen")
                    if listen is not None:
                        entry["listen"] = listen.get("address", "")

                result.append(entry)

        except Exception as e:
            logger.error("Failed to extract device info: %s", e)

        return result

    @timeit
    def _get_domain(self, domain_name: str = None, domain_id: int = None, domain_uuid: str = None) -> Optional[libvirt.virDomain]:
        """获取虚拟机对象

        Args:
            domain_name (str): 虚拟机名称
            domain_id (int): 虚拟机id
            domain_uuid (str): 虚拟机uuid

        Returns:
            Optional[libvirt.virDomain]: 虚拟机对象实例
        """
        try:
            if domain_id is not None:
                logger.debug(domain_id)
                return self.conn.lookupByID(domain_id)
            if domain_name is not None:
                return self.conn.lookupByName(domain_name)
            if domain_uuid is not None:
                return self.conn.lookupByUUIDString(domain_uuid)
            logger.error("You must specify one of: domain_name, domain_id, or domain_uuid.")
        except libvirt.libvirtError as e:
            logger.error(f"Failed to find domain: {e}")
        return None

    @timeit
    def list_domains(self) -> List[Tuple[int, str]]:
        """获取虚拟机ID和名称列表

        Args:
            only_running (bool, optional): True为列出当前正在运行的虚拟机，反之列出所有虚拟机（包括未运行的）

        Returns:
            List[Tuple[int, str]]: 虚拟机ID和名称序列化列表
            - vm_id (int): 虚拟机id
            - vm_uuid (str): 虚拟机uuid
            - vm_name (str): 虚拟机名称
        """
        result: List[Tuple[int, str]] = []
        
        try:
            # 获取所有domain对象
            domains = self.conn.listAllDomains()
            for dom in domains:
                domain_id = dom.ID()  # 运行中是正整数，关机是 -1
                result.append({
                    "vm_id": domain_id if domain_id != -1 else None,
                    "vm_uuid": dom.UUIDString(),
                    "vm_name": dom.name()
                })
        except libvirt.libvirtError as e:
            logger.error("Error listing domains: %s", e)

        return result

    @handle_libvirt_error
    @timeit
    def domain_info(self, domain: libvirt.virDomain, device_types: Optional[List[str]] = None) -> Dict:
        """获取虚拟机核心信息，可选获取指定类型设备信息

        Args:
            domain (libvirt.virDomain): 虚拟机对象实例
            device_types (Optional[List[str]], optional): 设备类型，目前有disk, interface, graphics三种选项
        
        Returns:
            Dict: 虚拟机核心信息序列化字典
            - vm_name (str): 虚拟机名称
            - vm_id (int): 虚拟机id
            - vm_uuid (str): 虚拟机uuid
            - vm_state (str): 虚拟机状态
            - vm_max_memory (str): 虚拟机内存大小
            - vm_use_memory (str): 虚拟机内存大小
            - vm_vcpus (int): 虚拟机vcpu数量
        """
        try:            
            data = {
                "vm_name": domain.name(),
                "vm_id": domain.ID() if domain.ID() != -1 else None,
                "vm_uuid": domain.UUIDString(),
                "vm_state": VM_STATES.get(domain.info()[0], "unknown"),
                "is_active": bool(domain.isActive()),
                "is_persistent": bool(domain.isPersistent),
                "is_auto_start": bool(domain.autostart()),
                "vm_max_memory": f"{bytes_to_mib(domain.info()[1])}GiB",
                "vm_use_memory": f"{bytes_to_mib(domain.info()[2])}GiB",
                "vm_vcpus": domain.info()[3],
                "vm_os": domain.OSType(),
                "vm_snapshot": domain.hasCurrentSnapshot(),
                "vm_save_img": domain.hasManagedSaveImage()
            }

            if device_types:
                data["vm_devices"] = self.extract_device_info(domain, device_types)

            return data
        
        except (libvirt.libvirtError, ValueError) as e:
            logger.error(f"Failed to get domain info: {e}")
            return None

    @handle_libvirt_error
    @timeit
    def create(self, domain: libvirt.virDomain) -> bool:
        """创建(开启)虚拟机

        Args:
            domain (libvirt.virDomain): libvirt虚拟机对象
        Returns:
            bool: True为创建成功，反之创建失败
        """
        return domain.create()

    # 复用 create_domain 
    def start(self, *args, **kwargs) -> bool:
        return self.create(*args, **kwargs)

    @handle_libvirt_error
    @timeit
    def shutdown(self, domain: libvirt.virDomain) -> bool:
        """关闭虚拟机

        Args:
            domain (libvirt.virDomain): libvirt虚拟机对象

        Returns:
            bool: True为关闭成功，反之关闭失败
        """
        return domain.shutdown()

    @handle_libvirt_error
    @timeit
    def destroy(self, domain: libvirt.virDomain) -> bool:
        """强制关闭虚拟机

        Args:
            domain (libvirt.virDomain): libvirt虚拟机对象

        Returns:
            bool: True为关闭成功，反之关闭失败
        """
        return domain.destroy()

    @handle_libvirt_error
    @timeit
    def pause(self, domain: libvirt.virDomain) -> bool:
        """挂起虚拟机

        Args:
            domain (libvirt.virDomain): libvirt虚拟机对象

        Returns:
            bool: True为挂起成功，反之挂起失败
        """
        return domain.suspend()

    @handle_libvirt_error
    @timeit
    def resume(self, domain: libvirt.virDomain) -> bool:
        """恢复虚拟机

        Args:
            domain (libvirt.virDomain): libvirt虚拟机对象

        Returns:
            bool: True为恢复成功，反之恢复失败
        """
        return domain.resume()

    @handle_libvirt_error
    @timeit
    def reboot(self, domain: libvirt.virDomain) -> bool:
        """重启虚拟机

        Args:
            domain (libvirt.virDomain): libvirt虚拟机对象

        Returns:
            bool: True为重启成功，反之重启失败
        """
        return domain.reboot()

    @handle_libvirt_error
    @timeit
    def reset(self, domain: libvirt.virDomain) -> bool:
        """重置虚拟机（硬重启）

        Args:
            domain (libvirt.virDomain): libvirt虚拟机对象

        Returns:
            bool: True为重启成功，反之重启失败
        """
        return domain.reset()

    @handle_libvirt_error
    @timeit
    def send_ctrl_alt_del(self, domain: libvirt.virDomain) -> bool:
        """发送 Ctrl+Alt+Delete 至虚拟机（重启）

        Args:
            domain (libvirt.virDomain): libvirt虚拟机对象

        Returns:
            bool: True为发送成功，反之发送失败
        """
        return domain.sendKey(codeset=0, holdtime=0, keycodes=[29, 56, 111], nkeycodes=3)

    @handle_libvirt_error
    @timeit
    def undefine(self, domain: libvirt.virDomain) -> bool:
        """删除虚拟机

        Args:
            domain (libvirt.virDomain): libvirt虚拟机对象

        Returns:
            bool: True为删除成功，反之删除失败
        """
        return domain.undefine()

    def _set_autostart(self, domain: libvirt.virDomain, val: int) -> bool:
        """
        设置虚拟机开机自启（宿主机开机时一并启动）

        Args:
            domain (libvirt.virDomain): libvirt虚拟机对象
            val (int): 1 表示开启，0 表示关闭

        Returns:
            bool: True 为设置成功，反之设置失败
        """
        return domain.setAutostart(val) == 0

    @handle_libvirt_error
    @timeit
    def set_auto_start(self, domain: libvirt.virDomain, state: str = "on") -> bool:
        """
        设置虚拟机是否开机自启

        Args:
            domain (libvirt.virDomain): 虚拟机对象
            state (str): "on" 启用开机启动，"off" 禁用

        Returns:
            bool: 操作成功返回 True
        """
        if state not in ("on", "off"):
            raise ValueError("state must be 'on' or 'off'")
        return self._set_autostart(domain, 1 if state == "on" else 0)

    @handle_libvirt_error
    @timeit
    def set_memory(self, domain: libvirt.virDomain, memory: int, config=False) -> bool:
        """设置虚拟机最大内存

        Args:
            domain (libvirt.virDomain): libvirt虚拟机对象
            memory (int): 内存大小（单位MB）

        Returns:
            bool: True为设置成功，反之设置失败
        """
        if VM_STATES.get(domain.info()[0], "unknown") != "shut off":
            logger.error(f"Cannot set memory. Shutdown domain {domain.name()} first")
            return False

        try:
            flags = libvirt.VIR_DOMAIN_MEM_MAXIMUM
            if config:
                flags |= libvirt.VIR_DOMAIN_AFFECT_CONFIG
            domain.setMemoryFlags(memory * 1024, flags)
            domain.setMemoryFlags(memory * 1024, libvirt.VIR_DOMAIN_AFFECT_CURRENT)
            logger.info(f"Domain {domain.name()} set memory: {memory} MB")
            return True
        except libvirt.libvirtError as e:
            logger.error(f"Set memory failed: {e}", )
            return False

    @handle_libvirt_error
    @timeit
    def set_vcpu(self, domain: libvirt.virDomain, vcpus: int) -> bool:
        """设置虚拟机vcpu数量

        Args:
            domain (libvirt.virDomain): libvirt虚拟机对象
            vcpus (int): vcpu数量

        Returns:
            bool: True为设置成功，反之设置失败
        """
        if VM_STATES.get(domain.info()[0], "unknown") != "shut off":
            logger.error(f"Cannot set vCPUs. Shutdown domain {domain.name()} first")
            return False

        try:
            domain.setVcpusFlags(vcpus, libvirt.VIR_DOMAIN_VCPU_MAXIMUM | libvirt.VIR_DOMAIN_AFFECT_CONFIG)
            domain.setVcpusFlags(vcpus, libvirt.VIR_DOMAIN_AFFECT_CURRENT)
            logger.info(f"Domain {domain.name()} set vcpus to {vcpus}")
            return True
        except libvirt.libvirtError as e:
            logger.error(f"Set vcpus failed: {e}")
            return False

    @handle_libvirt_error
    @timeit
    def save(self, domain: libvirt.virDomain, save_path: str) -> bool:
        """保存当前虚拟机的内存和 CPU 状态（暂停虚拟机，相当于休眠）
        
        注意：此操作不保存磁盘内容，保存后虚拟机会关闭，可通过 restore() 恢复

        Args:
            domain (libvirt.virDomain): libvirt虚拟机对象
            save_path (str): 保存路径

        Returns:
            bool: True为保存成功，反之保存失败
        """
        if VM_STATES.get(domain.info()[0], "unknown") == "shut off":
            logger.warning(f"Cannot save domain state, domain {domain.name()} is not running")
            return False
        try:
            domain.save(save_path)
            logger.info(f"Domain {domain.name()} state save to {save_path} successfully")
            return True
        except libvirt.libvirtError as e:
            logger.error(f"Domain {domain.name()} save failed: {e}")
            return False

    @timeit
    def restore(self, save_path: str) -> bool:
        """恢复虚拟机状态
        
        注意：此操作不包含磁盘

        Args:
            save_path (str): 虚拟机内存镜像保存路径

        Returns:
            bool: True为恢复成功，反之恢复失败
        """
        try:
            id = self.conn.restore(save_path)
            if id < 0:
                logger.error(f"Unable to restore domain from {save_path}")
                return False
            
            logger.info(f"Domain state restored from {save_path}")
            return True
        except libvirt.libvirtError as e:
            logger.error(f"Domain restore failed: {e}")
            return False

    @handle_libvirt_error
    @timeit
    def delete(self, domain: libvirt.virDomain) -> bool:
        """删除虚拟机

        Args:
            domain (libvirt.virDomain): libvirt虚拟机对象

        Returns:
            bool: True为删除成功，反之删除失败
        """
        if self.domain_state(domain)['domain_state'] == "running":
            if not self.destroy(domain):
                return False
        return self.undefine(domain)

    @timeit
    def domain_create(
        self,
        name: str,
        ram: int,
        vcpu: int,
        net_name: str,
        os_arch: str = "x86_64",
        emulator: str = "/usr/libexec/qemu-kvm",
        boot_disk: str = None,
        cdrom: str = '',
        running: bool = False) -> bool:
        """创建虚拟机
        
        Args:
            name (str): 虚拟机名称
            ram (int): 虚拟机内存（单位MiB）
            vcpu (int): 虚拟机vcpu
            net_name (str): 虚拟网络名称
            os_arch (str): 虚拟机架构，默认x86_64
            emulator (str): kvm仿真器
            boot_disk (str): 启动磁盘
            cdrom (str): 光驱
        
        Returns:
            bool: True为创建成功，反之创建失败
        """
        xml = f"""
        <domain type='kvm'>
            <name>{name}</name>
            <memory unit='MiB'>{ram}</memory>
            <currentMemory unit='MiB'>{ram}</currentMemory>
            <vcpu placement='static'>{vcpu}</vcpu>
            <cputune>
                <shares>1024</shares>
            </cputune>
            <sysinfo type='smbios'>
                <system>
                <entry name='manufacturer'>NorthSky</entry>
                <entry name='product'>NorthSky</entry>
                <entry name='version'>2025-06-v0.1.0</entry>
                <entry name='family'>Virtual Machine</entry>
                </system>
            </sysinfo>
            <os>
                <type arch='{os_arch}' machine='pc-i440fx-rhel7.2.0'>hvm</type>
                <boot dev='hd'/>
                <boot dev='cdrom'/>
                <smbios mode='sysinfo'/>
            </os>
            <features>
                <acpi/>
                <apic/>
            </features>
            <cpu mode='host-passthrough' check='none'>
            </cpu>
            <clock offset='utc'>
                <timer name='pit' tickpolicy='delay'/>
                <timer name='rtc' tickpolicy='catchup'/>
                <timer name='hpet' present='no'/>
            </clock>
            <on_poweroff>destroy</on_poweroff>
            <on_reboot>restart</on_reboot>
            <on_crash>destroy</on_crash>
            <devices>
                <emulator>{emulator}</emulator>
                <disk type='file' device='disk'>
                    <driver name='qemu' type='qcow2' cache='none'/>
                    <source file='{boot_disk}'/>
                    <target dev='vda' bus='virtio'/>
                    <address type='pci' domain='0x0000' bus='0x00' slot='0x04' function='0x0'/>
                </disk>
                <disk type='file' device='cdrom'>
                    <driver name='qemu' type='raw'/>
                    <source file='{cdrom}'/>
                    <target dev='hdb' bus='ide'/>
                </disk>
                <controller type='usb' index='0' model='piix3-uhci'>
                    <address type='pci' domain='0x0000' bus='0x00' slot='0x01' function='0x2'/>
                </controller>
                <interface type='network'>
                    <source network='{net_name}'/>
                    <model type='virtio'/>
                </interface>
                <serial type='pty'>
                    <target type='isa-serial' port='0'>
                        <model name='isa-serial'/>
                    </target>
                </serial>
                <console type='pty'>
                    <target type='serial' port='0'/>
                </console>
                <input type='tablet' bus='usb'>
                    <address type='usb' bus='0' port='1'/>
                </input>
                <input type='mouse' bus='ps2'/>
                <input type='keyboard' bus='ps2'/>
                <graphics type='vnc' port='-1' autoport='yes' listen='0.0.0.0'>
                    <listen type='address' address='0.0.0.0'/>
                </graphics>
                <video>
                    <model type='qxl' vram='16384' heads='1' primary='yes'/>
                    <address type='pci' domain='0x0000' bus='0x00' slot='0x02' function='0x0'/>
                </video>
                <memballoon model='virtio'>
                    <stats period='10'/>
                    <address type='pci' domain='0x0000' bus='0x00' slot='0x05' function='0x0'/>
                </memballoon>
            </devices>
        </domain>
        """
        try:
            domain = self.conn.defineXML(xml)
            if running:
                domain.create()
                logger.info(f"Create virtual machine {name} success")
                return True
            else:
                logger.info(f"Create virtual machine {name} success, but it still stopping")
                return True
        except libvirt.libvirtError as e:
            logger.error(f"Failed to create virtual machine {name}: {e}")
            return False

    @handle_libvirt_error
    @timeit
    def domain_cputime(self, domain: libvirt.virDomain, interval: float = 1.0) -> Dict:
        """获取虚拟机单位时间内的 CPU 占用率百分比（范围 0~100% * vCPUs）

        Args:
            domain (libvirt.virDomain): 虚拟机对象实例
            interval (float, optional): 采样时间（单位s），默认1.0

        Returns:
            Dict: 虚拟机自启动以来累计的"CPU"时间与在刚才"n"秒采样时间内，平均使用了整个宿主机"CPU"的百分比。
            - cputime (int): CPU启动累计时间，单位ns（纳秒）
            - cputime_percent (str): 宿主机CPU百分比
        """
        try:
            host_cpus = self.conn.getInfo()[2]

            # 第一次采样
            start_time = domain.info()[4]  # 纳秒
            time.sleep(interval)
            # 第二次采样
            end_time = domain.info()[4]  # 纳秒

            delta_ns = end_time - start_time
            delta_seconds = delta_ns / 1e9

            # 单位时间内虚拟机用掉的 CPU 秒数 / 实际总时间
            # 注意：总核心数越多，占比越低
            cpu_percent = (delta_seconds / interval) * 100 / host_cpus

            return {
                'cputime': end_time,
                'cputime_percent': f"{round(cpu_percent, 2)}%"
            }

        except libvirt.libvirtError as e:
            logger.error(f"Failed to read cputime for domain {domain.name()}: {e}")
            return []

    @handle_libvirt_error
    @timeit
    def domain_state(self, domain: libvirt.virDomain) -> str:
        """获取虚拟机状态

        Args:
            domain (libvirt.virDomain): 虚拟机对象实例

        Returns:
            str: 虚拟机运行状态
            - running
            - shut off
            - ...
        """
        try:
            state = VM_STATES.get(domain.state()[0], "unknown")
            logger.info(f"Getting domain {domain.name()} state: {state}")
            return {"domain_state": state}
        except libvirt.libvirtError as e:
            logger.error(f"Failed to get domain state: {e}")
            return {e}

    @handle_libvirt_error
    @timeit
    def domain_ipaddrs(self, domain: libvirt.virDomain) -> Dict:
        """获取虚拟机网卡信息

        Args:
            domain (libvirt.virDomain): 虚拟机对象实例

        Returns:
            Dict: 虚拟机网卡信息
            - 虚拟机网卡
                - mac_address (str): 虚拟机网卡mac地址
                - addresses (dict): 虚拟机网卡IP地址序列化字典
                    - addr (str): 虚拟机网卡IP地址
                    - prefix (int): 虚拟机网卡IP子网掩码
                    - type (str): 虚拟机网卡IP地址类型
        """
        try:
            stats = domain.interfaceAddresses(libvirt.VIR_DOMAIN_INTERFACE_ADDRESSES_SRC_LEASE)
            result = {}
            for iface_name, val in stats.items():
                result[iface_name] = {
                    "mac_address": val.get("hwaddr", ""),
                    "addresses": [
                        {
                            "addr": addr.get("addr", ""),
                            "prefix": addr.get("prefix", ""),
                            "type": "ipv4" if addr.get("type") == 0 else "ipv6"
                        }
                        for addr in val.get("addrs", [])
                    ]
                }
            logger.info(f"Getting domain {domain.name()} ipaddres")
            return result

        except libvirt.libvirtError as e:
            logger.warning(f"Failed to get domain {domain.name()} ipaddress: {e}, please start domain and try again later")
            return {}

    @handle_libvirt_error
    @timeit
    def domain_netstats(self, domain: libvirt.virDomain, to_mib: bool = False) -> Dict:
        """获取虚拟机网卡网络状态

        Args:
            domain (libvirt.virDomain): 虚拟机对象实例

        Returns:
            Dict: 虚拟机网卡网络状态
            - rx_bytes (int)： 接收字节大小
            - rx_packets (int): 接收数据包数量
            - rx_errs (int): 接收错误数量
            - rx_drop (int): 接收丢包数量
            - tx_bytes (int): 传出字节大小
            - tx_packets (int): 传出数据包大小
            - tx_errs (int): 传出错误数量
            - tx_drop (int): 传出丢包数量
        """
        nics = self.domain_info(domain, device_types=["interface"])["vm_devices"]
        
        for nic in nics:
            if 'target' not in nic:
                logger.warning(f"Interface entry missing 'target', please start domain and try again later")
                return False  # 早退逻辑：有一个不规范就退出
            
            target = nic['target']
            try:
                stats = domain.interfaceStats(target)  # 返回一个 8 元组
                NET_STATES['rx_bytes']   += stats[0] 
                NET_STATES['rx_packets'] += stats[1]
                NET_STATES['rx_errs']    += stats[2]
                NET_STATES['rx_drop']    += stats[3]
                NET_STATES['tx_bytes']   += stats[4]
                NET_STATES['tx_packets'] += stats[5]
                NET_STATES['tx_errs']    += stats[6]
                NET_STATES['tx_drop']    += stats[7]
                logger.info(f"Getting domain {domain.name()} nic state")
                
            except libvirt.libvirtError:
                logger.error(f"Failed to get domain {domain.name()} nic state")
                continue  # 忽略无法统计的接口

        if to_mib:
            NET_STATES['rx_bytes_mib'] = bytes_to_mib(NET_STATES['rx_bytes'])
            NET_STATES['tx_bytes_mib'] = bytes_to_mib(NET_STATES['tx_bytes'])

        return NET_STATES

    @handle_libvirt_error
    @timeit
    def domain_diskstats(self, domain: libvirt.virDomain, to_mib: bool = False) -> Dict:
        """获取虚拟机磁盘状态

        Args:
            domain (libvirt.virDomain): 虚拟机对象实例

        Returns:
            Dict: 虚拟机磁盘状态
            - rd_req (int): 磁盘读取请求
            - rd_bytes (int): 磁盘读取字节
            - wr_req (int): 磁盘写入请求
            - wr_bytes (int): 磁盘写入字节
            - errs (int): 磁盘错误数量
        """
        disks = self.domain_info(domain, device_types=["disk"])["vm_devices"]
        for disk in disks:
            target = disk['target']
            try:
                stats = domain.blockStats(target)
                BLOCK_STATES['rd_req']   += stats[0]
                BLOCK_STATES['rd_bytes'] += stats[1]
                BLOCK_STATES['wr_req']   += stats[2]
                BLOCK_STATES['wr_bytes'] += stats[3]
                BLOCK_STATES['errs']     += stats[4]

                
                logger.info(f"Getting domain {domain.name()} disk state")
                
            except libvirt.libvirtError as e:
                logger.warning(f"Failed to get domain {domain.name()} disk state: {e}, please start domain and try again later")
                continue

        if to_mib:
            BLOCK_STATES['rd_bytes_mib'] = bytes_to_mib(BLOCK_STATES['rd_bytes'])
            BLOCK_STATES['wr_bytes_mib'] = bytes_to_mib(BLOCK_STATES['wr_bytes'])

        return BLOCK_STATES

    @handle_libvirt_error
    @timeit
    def domain_hostname(self, domain: libvirt.virDomain) -> str:
        """获取虚拟机hostname

        Args:
            domain (libvirt.virDomain): 虚拟机对象实例

        Returns:
            str: 虚拟机主机名（当虚拟机关机或没有qemu-agent时为None）
            - localhost.novalocal
            - None
        """
        try:
            hostname = domain.hostname()
            return {"domain_hostname": hostname}
        except libvirt.libvirtError as e:
            logger.warning(f"Failed to get domain hostname: {e}, start domain or qemu agent not configured or current libvirt version doesn't support this function")
            return {"domain_hostname": None}

    @handle_libvirt_error
    @timeit
    def domain_full_stats(self, domain: libvirt.virDomain, to_mib: bool = False) -> Dict:
        """获取虚拟机所有信息

        Args:
            domain (libvirt.virDomain): 虚拟机对象实例

        Returns:
            Dict: 虚拟机所有信息
            - vm_name (str): 虚拟机名称
            - vm_hostname (str): 虚拟机主机名
            - state (str): 虚拟机状态
            - cpu_uptime (dict): 虚拟机cpu时间
            - net (dict): 虚拟机网卡状态
            - disk (dict): 虚拟机磁盘
            - ipaddrs (dict): 虚拟机ip信息
        """
        return {
            'vm_name': domain.name(),
            'vm_hostname': self.domain_hostname(domain),
            'state': self.domain_state(domain),
            'cpu_uptime': self.domain_cputime(domain),
            'net': self.domain_netstats(domain, to_mib=True) if to_mib else self.domain_netstats(domain),
            'disk': self.domain_diskstats(domain, to_mib=True) if to_mib else self.domain_diskstats(domain),
            'ipaddrs': self.domain_ipaddrs(domain)
        }
