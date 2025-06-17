import libvirt
from typing import Dict, Any
from xml.dom import minidom
from utils.connect import LibvirtConnector
from utils.logger import logger
from utils.functions import timeit
from lxml import etree


class HostManager:
    def __init__(self, conn: libvirt.virConnect):
        """初始化host连接

        Args:
            conn (libvirt.virConnect): libvirt连接对象
        """
        self.conn = conn

    @timeit
    def get_hostname(self) -> str:
        """获取宿主机hostname信息

        Returns:
            str: 宿主机hostname信
        """
        try:
            hostname = self.conn.getHostname()
            return {"hostname": hostname}
        except libvirt.libvirtError as e:
            logger.error(f"Failed to get hostname: {e}")
            return None

    @timeit
    def get_host_cpu_info(self) -> Dict:
        """获取宿主机cpu信息

        Returns:
            Dict: 宿主机cpu信息字典
            - arch (str): CPU架构
            - model (str): CPU型号
            - vendor (str): CPU制造商
            - cpumhz (int): 当前CPU运行频率
            - numa_nodes (int): CPU numa节点
            - sockets (int): CPU 插槽
            - cores (int): CPU 核心数量
            - threads (int): CPU 线程
        """
        try:
            caps_xml = self.conn.getCapabilities()
            caps = minidom.parseString(caps_xml)
            host = caps.getElementsByTagName('host')[0]
            cpu = host.getElementsByTagName('cpu')[0]

            arch = cpu.getElementsByTagName('arch')[0].firstChild.nodeValue
            model = cpu.getElementsByTagName('model')[0].firstChild.nodeValue
            vendor = cpu.getElementsByTagName('vendor')[0].firstChild.nodeValue

            cells = host.getElementsByTagName('cells')[0]
            cpus = cells.getElementsByTagName('cpu')
            total_cpus = cpus.length
            numa_nodes = int(cells.getAttribute('num'))

            socket_ids = {cpu.getAttribute('socket_id') for cpu in cpus}
            core_ids = {cpu.getAttribute('core_id') for cpu in cpus}
            
            cpumhz = self.conn.getInfo()[3]
            
        except libvirt.libvirtError as e:
            logger.error("Failed to request capabilities: %s", e)
        
        return {
            "arch": arch,
            "model": model,
            "vendor": vendor,
            "cpumhz": cpumhz,
            "numa_nodes": numa_nodes,
            "sockets": len(socket_ids),
            "cores": len(core_ids),
            "threads": total_cpus
        }

    @timeit
    def get_numa_memory_info(self) -> Dict[str, Any]:
        """获取numa节点内存信息、使用情况、虚拟机绑定状态

        Returns:
            Dict[str, Any]: numa节点内存信息字典
            - numa_nodes (dict): 当前numa节点id
            - node_memory (dict): 当前numa节点总内存大小与空闲内存
            - domain (dict): 虚拟机与numa绑定状态
        """
        try:
            caps_xml = self.conn.getCapabilities()
            doms = self.conn.listAllDomains(libvirt.VIR_CONNECT_LIST_DOMAINS_ACTIVE)
        except libvirt.libvirtError as e:
            logger.error("Failed to get capabilities or domains: %s", e)
            return {}

        try:
            caps_root = etree.fromstring(caps_xml.encode())
            node_elements = caps_root.xpath("//cells/cell")
            node_ids = [int(cell.attrib["id"]) for cell in node_elements]

            node_mem_stats = {
                node_id: self.conn.getMemoryStats(node_id)
                for node_id in node_ids
            }

            # 处理开启 strict NUMA 绑定策略的虚拟机
            doms_strict = [
                dom for dom in doms
                if dom.numaParameters().get("numa_mode") == libvirt.VIR_DOMAIN_NUMATUNE_MEM_STRICT
            ]

            doms_numa_binding = {}
            for dom in doms_strict:
                dom_xml = dom.XMLDesc()
                dom_root = etree.fromstring(dom_xml.encode())

                binding_info = {}
                memory_node = dom_root.find("memory")
                numa_memory = dom_root.find("numatune/memory")

                if memory_node is not None:
                    binding_info["memory"] = {
                        "size": int(memory_node.text),
                        "pin": numa_memory.attrib.get("nodeset", "") if numa_memory is not None else ""
                    }

                for memnode in dom_root.findall("numatune/memnode"):
                    cellid = memnode.attrib.get("cellid", "")
                    nodeset = memnode.attrib.get("nodeset", "")
                    size_node = dom_root.find(f"./cpu/numa/cell[@id='{cellid}']")
                    memsize = int(size_node.attrib.get("memory", "0")) if size_node is not None else 0

                    binding_info[cellid] = {
                        "size": memsize,
                        "pin": nodeset
                    }

                doms_numa_binding[dom.name()] = binding_info

        except Exception as e:
            logger.error("Failed to parse NUMA stats: %s", e)
            return {}

        return {
            "numa_nodes": node_ids,
            "node_memory": {
                node_id: {
                    "total": f"{mem.get("total", 0) // 1024}MiB",
                    "free": f"{mem.get("free", 0) // 1024}MiB"
                } for node_id, mem in node_mem_stats.items()
            },
            "domains": doms_numa_binding
        }

    @timeit
    def get_host_full_info(self) -> Dict[str, Any]:
        """获取宿主机所有信息

        Returns:
            Dict[str, Any]: 宿主机所有信息
            - hostname (str): 宿主机名称
            - cpu_detail (dict): CPU 相关信息
            - numa_detail (dict): numa 节点相关信息
        """
        return {
            "hostname": self.get_hostname(),
            "cpu_detail": self.get_host_cpu_info(),
            "numa_detail": self.get_numa_memory_info()
        }


# 示例输出
if __name__ == "__main__":
    conn = LibvirtConnector().connect()
    host = HostManager(conn)
    print(host.get_host_full_info())