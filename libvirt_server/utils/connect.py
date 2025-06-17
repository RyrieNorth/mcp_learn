import libvirt
from typing import Optional, Callable, Tuple
from utils.logger import logger
from utils.env_utils import get_env_var


class LibvirtConnector:
    """连接Libvirt
    """
    def __init__(
        self,
        uri: str = None,
        readonly: bool = False,
        auth: Optional[Tuple[Tuple[int, ...], Callable[[int, str, str, int], str]]] = None
    ):
        """初始化Libvirt连接对象

        Args:
            uri (str, optional): 服务器地址
            readonly (bool, optional): 是否只读
            auth (Optional[Tuple[Tuple[int, ...], Callable[[int, str, str, int], str]]], optional): 是否认证
        """
        self.uri = uri or get_env_var("LIBVIRT_SERVER", "qemu:///system")
        self.readonly = readonly
        self.auth = auth
        self.conn: Optional[libvirt.virConnect] = None
        
    def connect(self) -> Optional[libvirt.virConnect]:
        """创建Libvirt连接对象

        Returns:
            Optional[libvirt.virConnect]: Libvirt连接对象
        """
        try:
            if self.readonly:
                self.conn = libvirt.openReadOnly(self.uri)
            elif self.auth:
                self.conn = libvirt.openAuth(self.uri, self.auth)
            else:
                self.conn = libvirt.open(self.uri)
            
            if self.conn is None:
                logger.error("Failed to open libvirt connection")
            else:
                logger.info(f"Libvirt connection ({"Auth" if self.auth else ("RO" if self.readonly else "RW")}) established: {self.uri}")                
             
            return self.conn
           
        except libvirt.libvirtError as e:
            logger.error("Connection to %s failed: %s", self.uri, e)
            return None
        
    def close(self):
        """释放连接
        """
        if self.conn:
            try:
                self.conn.close()
                logger.info("Libvirt connection closed")
            except libvirt.libvirtError as e:
                logger.warning(f"Error closing libvirt connection: {e}")
            self.conn = None