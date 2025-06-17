from utils.connect import LibvirtConnector
from utils.console import LibvirtConsole
from utils.host_manager import HostManager
from utils.net_manager import NetManager
from utils.net_manager import BridgeManager
from utils.pool_manager import PoolManager
from utils.vm_manager import VMManager
from utils.vol_manager import VolManager
from utils.logger import logger
from utils.functions import run_cmd


class LibvirtServer:
    def __init__(self, uri=None, readonly=False, auth=None):
        """
        创建 LibvirtServer 实例。
        可传入自定义连接参数：uri, readonly, auth。
        """
        self.connector = LibvirtConnector(uri=uri, readonly=readonly, auth=auth)
        self.conn = self.connector.connect()

        # 初始化各功能模块
        self.console = LibvirtConsole()
        self.host    = HostManager(self.conn)
        self.net     = NetManager(self.conn)
        self.br      = BridgeManager(run_cmd)
        self.pool    = PoolManager(self.conn)
        self.vm      = VMManager(self.conn)
        self.vol     = VolManager(self.conn)

    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("Disconnected from libvirt")

    def __del__(self):
        self.close()
