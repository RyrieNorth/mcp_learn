import libvirt
import subprocess
from utils.connect import LibvirtConnector
from utils.env_utils import get_env_var
from utils.logger import logger
from utils.details import POOL_STATES
from utils.functions import timeit
from typing import List, Dict, Optional


def bytes_to_gib(byte_value: int) -> float:
    """字节换算，Byte to GiB

    Args:
        byte_value (int): 字节值

    Returns:
        float: 返回浮点数，取小数点前两位
    """
    return round(byte_value / (1024 ** 3), 2)

class PoolManager:
    def __init__(self, conn: libvirt.virConnect):
        self.conn = conn

    @timeit
    def list_pools(self) -> Optional[List[Dict[str, str]]]:
        """列出所有存储池

        Returns:
            Optional[List[Dict[str, str]]]: 存储池列表
            - [{'pool': 'opt'}]
        """
        result: List = []
        try:
            pools = self.conn.listAllStoragePools(0)
            if not pools:
                logger.warning(f"Failed to locate any StoragePool, StoragePool was none")
                return None
            for pool in pools:
                result.append({"pool_name": pool.name(), "pool_uuid": pool.UUIDString()})
        except libvirt.libvirtError as e:
            logger.error(f"Failed to locate any StoragePool object: {e}")
            return []
        
        return result

    @timeit
    def pool_info(self, pool_name: str = None, pool_uuid: str = None) -> Dict:
        """获取存储池的详细信息

        Args:
            pool (libvirt.virStoragePool): _description_

        Returns:
            Dict: 返回存储池的详细信息字典
            - pool_name (str): 存储池名称
            - pool_uuid (str): 存储池uuid
            - autostart (bool): 是否开机自启
            - is_active (bool): 是否运行中
            - is_persistent (bool): 是否持久化
            - num_vols (int): 存储池中的卷数量（若存储池未运行或不存在，返回None）
            - pool_state (str): 存储池运行状态
            - pool_capacity (str): 存储池总大小
            - pool_allocation (str): 存储池使用情况
            - pool_available (str): 存储池可用大小
        """
        if pool_name and (pool_uuid is not None):
            raise ValueError("Please provide only one of pool_name or pool_uuid")

        if pool_uuid is None and pool_name is not None:
            if '-' in pool_name:
                pool_uuid, pool_name = pool_name, None

        if not pool_name and not pool_uuid:
            raise ValueError("Either pool_name or pool_uuid must be provided")

        try:
            if pool_name:
                pool = self.conn.storagePoolLookupByName(pool_name)
            elif pool_uuid:
                pool = self.conn.storagePoolLookupByUUIDString(pool_uuid)
                            
            info = pool.info()
            state = POOL_STATES.get(info[0], "unknown")
            capacity = info[1]
            allocation = info[2]
            available = info[3]
            
        except libvirt.libvirtError as e:
            logger.warning(f"Failed to get pool info: {e}")
            state = "inactive"
            capacity = allocation = available = 0

        try:
            num_vols = pool.numOfVolumes()
        except libvirt.libvirtError as e:
            logger.warning(f"Failed to get volume count for pool '{pool.name()}': {e}")
            num_vols = 0

        try:
            return {
                "pool_name": pool.name(),
                "pool_uuid": pool.UUIDString(),
                "autostart": bool(pool.autostart()),
                "is_active": bool(pool.isActive()),
                "is_persistent": bool(pool.isPersistent()),
                "num_vols": num_vols,
                "pool_state": state,
                "pool_capacity": f"{bytes_to_gib(capacity)}GiB",
                "pool_allocation": f"{bytes_to_gib(allocation)}GiB",
                "pool_available": f"{bytes_to_gib(available)}GiB"
            }
        except libvirt.libvirtError as e:
            logger.error(f"Failed to read metadata for pool: {e}")
            return {}

    def generate_pool_xml(self, pool_type: str, pool_name: str, pool_path: str, source: Optional[Dict] = None) -> str:
        """
        根据存储池类型生成对应的XML配置。
        
        参数说明:
        - pool_type: 存储池类型（如 dir, netfs, iscsi, logical, disk, fs）
        - pool_name: 存储池名称
        - pool_path: 挂载目标路径（<target><path>）
        - source: dict，包含不同类型存储池所需的source参数：
            - dir 类型不需要 source
            - netfs: {host: "1.2.3.4", dir: "/nfs/path", format: "auto"}
            - iscsi: {host: "hostname", device: "iqn..."}
            - logical: {name: "volume_group", format: "lvm2"}
            - disk: {device: "/dev/sdX", format: "dos/gpt/mac/..."}
            - fs: {device: "/dev/sdX", format: "ext4/xfs/auto/..."}
        """

        source_xml = ""
        if pool_type == "netfs" and source:
            source_xml = f"""
            <source>
                <host name='{source["host"]}'/>
                <dir path='{source["dir"]}'/>
                <format type='{source.get("format", "auto")}'/>
            </source>"""
        elif pool_type == "iscsi" and source:
            source_xml = f"""
            <source>
                <host name='{source["host"]}'/>
                <device path='{source["device"]}'/>
            </source>"""
        elif pool_type == "logical" and source:
            source_xml = f"""
            <source>
                <name>{source["name"]}</name>
                <format type='{source.get("format", "lvm2")}'/>
            </source>"""
        elif pool_type == "disk" and source:
            source_xml = f"""
            <source>
                <device path='{source["device"]}'/>
                <format type='{source.get("format", "dos")}'/>
            </source>"""
        elif pool_type == "fs" and source:
            source_xml = f"""
            <source>
                <device path='{source["device"]}'/>
                <format type='{source.get("format", "auto")}'/>
            </source>"""

        xml = f"""
        <pool type='{pool_type}'>
            <name>{pool_name}</name>
            <capacity unit='bytes'>0</capacity>
            <allocation unit='bytes'>0</allocation>
            <available unit='bytes'>0</available>
            {source_xml}
            <target>
                <path>{pool_path}</path>
            </target>
        </pool>
        """
        return xml

    @timeit
    def create_pool(self, pool_type: str, pool_name: str, pool_path: str, source: Optional[Dict] = None) -> bool:
        """
        创建存储池（支持多种类型），返回是否成功。

        参数：
        - pool_type: 存储池类型
        - pool_name: 名称
        - pool_path: 挂载目标路径
        - source: 类型相关配置，详见 generate_pool_xml 的注解
        
        使用参考：
        
        - 创建一个 dir 类型存储池
        >>> create_pool("dir", "mypool", "uuid-001", "/data/images")

        - 创建一个 netfs 存储池（例如NFS）
        >>> create_pool("netfs", "nfs_pool", "uuid-002", "/mnt/nfs", {
            "host": "192.168.1.200",
            "dir": "/nfs/storage",
            "format": "auto"
        })

        - 创建一个 iscsi 存储池
        >>> create_pool("iscsi", "iscsi_pool", "uuid-003", "/data/iscsi", {
            "host": "iscsi-host",
            "device": "iqn.2025-06.cn.ryrie:client"
        })
        """
        supported_types = {"dir", "netfs", "iscsi", "logical", "disk", "fs"}

        if pool_type not in supported_types:
            logger.error(f"Unsupported pool type: {pool_type}")
            return False

        if pool_type == "dir":
            cmd = f"ssh root@{get_env_var('LIBVIRT_HOST')} mkdir -p {pool_path}"
            logger.info(f"Ensuring remote folder {pool_path} exists")
            try:
                subprocess.run(cmd, shell=True, check=True)
            except subprocess.CalledProcessError as e:
                logger.error(f"Failed to create remote directory: {e}")
                return False

        try:
            pool_xml = self.generate_pool_xml(pool_type, pool_name, pool_path, source)
            pool = self.conn.storagePoolDefineXML(pool_xml)
            pool.setAutostart(1)
            pool.create()
            logger.info(f"Create storage pool '{pool_name}' success")
            return True
        except libvirt.libvirtError as e:
            logger.error(f"Failed to create storage pool '{pool_name}': {e}")
            return False

    @timeit
    def delete_pool(self, pool_name: str = None, pool_uuid: str = None) -> bool:
        """删除存储池

        Args:
            pool_name (str): 存储池名称

        Returns:
            bool: True未删除成功，反之删除失败
        """
        if pool_name and (pool_uuid is not None):
            raise ValueError("Please provide only one of pool_name or pool_uuid")

        if pool_uuid is None and pool_name is not None:
            if '-' in pool_name:
                pool_uuid, pool_name = pool_name, None

        if not pool_name and not pool_uuid:
            raise ValueError("Either pool_name or pool_uuid must be provided")

        try:
            if pool_name:
                pool = self.conn.storagePoolLookupByName(pool_name)
            elif pool_uuid:
                pool = self.conn.storagePoolLookupByUUIDString(pool_uuid)

            if pool.isActive():
                pool.destroy()

            pool.undefine()
            logger.info(f"Deleted storage pool '{pool_name}' successfully")
            return True

        except libvirt.libvirtError as e:
            logger.error(f"Failed to delete storage pool '{pool_name}': {e}")
            return False
