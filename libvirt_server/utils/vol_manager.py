import libvirt
import os
from utils.connect import LibvirtConnector
from utils.logger import logger
from utils.details import VOLUME_TYPE
from utils.functions import timeit
from tqdm import tqdm
from typing import List, Dict, Any

def bytes_to_gib(byte_value: int) -> float:
    """字节转换，bytes to GiB

    Args:
        byte_value (int): 字节值

    Returns:
        float: GiB值
    """
    return round(byte_value / (1024 ** 3), 2)

# Copy from libvrt-python
"""
libvirt 流传输处理函数模块

该模块提供一组回调处理器，用于与 libvirt 的 virStream 接口交互，主要实现以下功能：

- bytesWriteHandler: 将接收到的数据写入指定文件描述符。
- bytesReadHandler: 从指定文件描述符读取指定字节数的数据。
- recvSkipHandler: 在接收过程中跳过一定长度的数据，并截断文件到当前位置。
- sendSkipHandler: 在发送过程中跳过一定长度的数据。
- holeHandler: 用于判断当前文件指针是否处于空洞区域，以及该区域的长度。

这些函数一般用于处理磁盘镜像、稀疏文件传输或远程迁移等需要基于 virStream 的 I/O 操作。
"""
def bytesWriteHandler(stream: libvirt.virStream, buf: bytes, opaque: int) -> int:
    """将数据写入文件描述符

    Args:
        stream (libvirt.virStream): libvirt流对象
        buf (bytes): 待写入的数据
        opaque (int): 文件描述符（通常是一个整数）

    Returns:
        int: 实际写入的字节数
    """
    fd = opaque
    return os.write(fd, buf)

def bytesReadHandler(stream: libvirt.virStream, nbytes: int, opaque: int) -> bytes:
    """从文件描述符读取数据

    Args:
        stream (libvirt.virStream): libvirt流对象
        nbytes (int): 要读取的字节数
        opaque (int): 文件描述符

    Returns:
        bytes: 读取的字节内容
    """
    fd = opaque
    return os.read(fd, nbytes)

def recvSkipHandler(stream: libvirt.virStream, length: int, opaque: int) -> None:
    """接收过程跳过指定长度，并截断文件到当前位置

    Args:
        stream (libvirt.virStream): libvirt流对象
        length (int): 要跳过的字节数
        opaque (int): 文件描述符
    """
    fd = opaque
    cur = os.lseek(fd, length, os.SEEK_CUR)
    return os.ftruncate(fd, cur)

def sendSkipHandler(stream: libvirt.virStream, length: int, opaque: int) -> int:
    """发送过程跳过指定长度

    Args:
        stream (libvirt.virStream): libvirt流对象
        length (int): 要跳过的字节数
        opaque (int): 文件描述符

    Returns:
        int: 跳过后新的文件偏移量
    """
    fd = opaque
    return os.lseek(fd, length, os.SEEK_CUR)

def holeHandler(stream: libvirt.virStream, opaque: int) -> List[Any]:
    """判断当前文件偏移量是否位于数据区或NULL区域，并返回该段长度

    Args:
        stream (libvirt.virStream): libvirt流对象
        opaque (int): 文件描述符

    Raises:
        e: ENXIO错误：没有找到指定设备或地址
        RuntimeError: 当前文件位置超出文件末尾
        RuntimeError: 未找到尾部NULL
        RuntimeError: 当前位置同时处于数据区和NULL，状态异常

    Returns:
        Dict: 列表 [inData, sectionLen]
        - inData: True 表示当前处于数据区，False 表示处于NULL
        - sectionLen: 当前段的长度（数据或NULL）
    """
    fd = opaque
    cur = os.lseek(fd, 0, os.SEEK_CUR)

    try:
        data = os.lseek(fd, cur, os.SEEK_DATA)
    except OSError as e:
        if e.errno != 6:    # ENXIO: No such device or address
            raise e
        else:
            data = -1
    # There are three options:
    # 1) data == cur;  @cur is in data
    # 2) data > cur; @cur is in a hole, next data at @data
    # 3) data < 0; either @cur is in trailing hole, or @cur is beyond EOF.
    
    # 三个选项：
    # 1) data == cur; @cur 位于数据中
    # 2) data > cur; @cur 位于NULL中，下一个数据位于 @data
    # 3) data < 0; 要么 @cur 位于尾部NULl中，要么 @cur 超过 EOF。
    if data < 0:
        # case 3
        inData = False
        eof = os.lseek(fd, 0, os.SEEK_END)
        if (eof < cur):
            raise RuntimeError("Current position in file after EOF: %d" % cur)
        sectionLen = eof - cur
    else:
        if (data > cur):
            # case 2
            inData = False
            sectionLen = data - cur
        else:
            # case 1
            inData = True

            # We don't know where does the next hole start. Let's find out.
            # Here we get the same options as above
            hole = os.lseek(fd, data, os.SEEK_HOLE)
            if hole < 0:
                # case 3. But wait a second. There is always a trailing hole.
                # Do the best what we can here
                raise RuntimeError("No trailing hole")

            if (hole == data):
                # case 1. Again, this is suspicious. The reason we are here is
                # because we are in data. But at the same time we are in a
                # hole. WAT?
                raise RuntimeError("Impossible happened")
            else:
                # case 2
                sectionLen = hole - data
    os.lseek(fd, cur, os.SEEK_SET)
    return [inData, sectionLen]


class VolManager:
    def __init__(self, conn: libvirt.virConnect):
        self.conn = conn
    
    @timeit
    def list_volumes(self, storage_pool: str) -> List[Dict[str, Any]]:
        """列出指定存储池中的卷

        Args:
            storage_pool (str): 存储池名称

        Returns:
            List[Dict[str, Any]]: 卷序列化列表
            - name: 卷名称
            - type：卷类型
            - capacity: 卷总大小
            - allocation: 卷可用大小
        """
        results: List[Dict[str, Any]] = []
        try:
            pool = self.conn.storagePoolLookupByName(storage_pool)
            vols = pool.listVolumes()
            for vol_name in vols:
                vol = pool.storageVolLookupByName(vol_name)
                info = vol.info()  # 返回 tuple: (type, capacity, allocation)
                results.append({
                    "name": vol_name,
                    "type": VOLUME_TYPE.get(info[0], "unknown"),
                    "path": vol.path(),
                    "capacity": f"{bytes_to_gib(info[1])}GiB",
                    "allocation": f"{bytes_to_gib(info[2])}GiB",
                })
        except libvirt.libvirtError as e:
            logger.error(f"Failed to list volumes: {e}")
        return results

    @timeit
    def create(self, storage_pool: str, vol_name: str, vol_size: int, vol_path: str) -> bool:
        """创建存储卷

        Args:
            storage_pool (str): 存储池名称
            vol_name (str): 卷名称
            vol_size (int): 卷大小，单位（MB）
            vol_path (str): 卷路径

        Returns:
            bool: True为创建成功，反之创建失败
        """
        
        xml = f"""
            <volume>
            <name>{vol_name}</name>
            <capacity unit="bytes">{vol_size * (1024 ** 2)}</capacity>
            <target>
                <path>{vol_path}</path>
            </target>
            </volume>
        """
        try:
            pool = self.conn.storagePoolLookupByName(storage_pool)
            pool.createXML(xml)
            logger.info(f"Create volume {vol_name} success")
            return True
        except libvirt.libvirtError as e:
            logger.error(f"Failed to create volume: {e}")
            return False

    @timeit
    def clone(self, storage_pool: str, src_vol_name: str, clone_vol_name: str) -> bool:
        """克隆卷

        Args:
            storage_pool (str): 存储池名称
            src_vol_name (str): 源存储卷名称
            clone_vol_name (str): 克隆卷名称

        Returns:
            bool: True为创建成功，反之创建失败
        """
        try:
            pool = self.conn.storagePoolLookupByName(storage_pool)
            src_vol = pool.storageVolLookupByName(src_vol_name)
            
            # 获取原始卷的信息
            vol_info = src_vol.info()
            vol_capacity = vol_info[1]  # capacity in bytes
            
            # 构造新的卷的 XML（可以自定义 clone 路径）
            clone_xml = f"""
                <volume>
                    <name>{clone_vol_name}</name>
                    <capacity unit="bytes">{vol_capacity}</capacity>
                    <target>
                        <format type="qcow2"/>
                    </target>
                </volume>
            """
            # 创建克隆卷
            pool.createXMLFrom(clone_xml, src_vol)
            logger.info(f"Clone volume '{src_vol_name}' to '{clone_vol_name}' success")
            return True
        
        except libvirt.libvirtError as e:
            logger.error(f"Failed to clone volume: {e}")
            return False

    @timeit
    def delete(self, storage_pool: str, vol_name: str) -> bool:
        """删除存储卷

        Args:
            storage_pool (str): 存储池名称
            vol_name (str): 卷名称

        Returns:
            bool: True为删除成功，反之删除失败
        """
        try:
            pool = self.conn.storagePoolLookupByName(storage_pool)
            vol = pool.storageVolLookupByName(vol_name)
            vol.wipe()
            vol.delete()
            logger.info(f"Delete volume {vol_name} success")
            return True
        except libvirt.libvirtError as e:
            logger.error(f"Failed to delete volume : {e}")
            return False

    @timeit
    def transfer(self, pool_name: str, vol_name: str, file_path: str, action: str) -> bool:
        """
        上传或下载存储卷

        Args:
            pool_name (str): 存储池名称
            volume_name (str): 存储卷名称
            file_path (str): 本地文件路径
            action (str): "upload" 或 "download"

        Returns:
            bool: True 表示成功，False 表示失败
        """
        try:
            pool = self.conn.storagePoolLookupByName(pool_name)
            vol = pool.storageVolLookupByName(vol_name)
            stream = self.conn.newStream()

            if action == "upload":
                total_size = os.path.getsize(file_path)  # 本地文件大小

            elif action == "download":
                vol_info = vol.info()
                total_size = vol_info[2] if vol_info[2] > 0 else vol_info[1]  # 卷的容量
            else:
                logger.error(f"Invalid action: {action}")
                return False
            
            progress = tqdm(total=total_size, unit='B', unit_scale=True, desc=f"{action.capitalize()} {vol_name}")
            transferred = [0]  # 用 list 是为了闭包可变引用

            def progress_read_handler(stream, nbytes, fd):
                data = os.read(fd, nbytes)
                transferred[0] += len(data)
                progress.update(len(data))
                return data

            def progress_write_handler(stream, data, fd):
                written = os.write(fd, data)
                transferred[0] += written
                progress.update(written)
                return written

            fd = None
            if action == "upload":
                fd = os.open(file_path, os.O_RDONLY)
                vol.upload(stream, 0, 0, libvirt.VIR_STORAGE_VOL_UPLOAD_SPARSE_STREAM)
                stream.sparseSendAll(progress_read_handler, holeHandler, sendSkipHandler, fd)

            elif action == "download":
                fd = os.open(file_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode=0o660)
                vol.download(stream, 0, 0, libvirt.VIR_STORAGE_VOL_DOWNLOAD_SPARSE_STREAM)
                stream.sparseRecvAll(progress_write_handler, recvSkipHandler, fd)

            else:
                logger.error(f"Invalid action: {action}")
                return False

            stream.finish()
            os.close(fd)
            progress.close()
            logger.info(f"{action.capitalize()} volume '{vol_name}' <-> {file_path} success.")
            return True

        except libvirt.libvirtError as e:
            logger.error(f"{action.capitalize()} failed: {e}")
            return False
        except Exception as e:
            logger.error(f"{action.capitalize()} unexpected error: {e}")
            return False

    def create_and_upload(self, pool_name: str, vol_name: str, vol_path: str, local_path: str) -> bool:
        """
        根据本地文件大小创建卷并上传

        Args:
            pool_name (str): 存储池名称
            vol_name (str): 卷名称
            vol_path (str): 卷存储路径
            local_path (str): 本地卷路径

        Returns:
            bool: True为创建成功，反之创建失败
        """
        try:
            # 获取本地文件大小（字节），转换为 MB，向上取整
            file_size = os.path.getsize(local_path)
            size_mb = (file_size + 1024 * 1024 - 1) // (1024 * 1024)

            logger.info(f"Local file size: {file_size} bytes -> {size_mb} MB")

            if not self.create(pool_name, vol_name, size_mb, vol_path):
                return False

            return self.transfer(pool_name, vol_name, local_path, action="upload")

        except Exception as e:
            logger.error(f"create_and_upload failed: {e}")
            return False

