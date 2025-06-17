import time
import libvirt
import functools
import paramiko
from utils.logger import logger
from utils.env_utils import get_env_var
from typing import Callable, Any, Optional, Union, Tuple

def handle_libvirt_error(func: Callable[..., Any]) -> Callable[..., bool]:
    """统一异常处理装饰器"""
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs) -> bool:
        try:
            domain = None
            if args and isinstance(args[0], libvirt.virDomain):
                domain = args[0]
                args = args[1:]  # 移除 domain 后续传参不重复

            else:
                domain_args = {
                    k: kwargs.pop(k)
                    for k in ("domain_name", "domain_id", "domain_uuid")
                    if k in kwargs
                }
                if domain_args:
                    domain = self._get_domain(**domain_args)
            
            if domain is None:
                logger.error("No domain could be resolved from parameters")
                return False

            result = func(self, domain, *args, **kwargs)
            
            if isinstance(result, dict):
                logger.info(f"Domain {domain.name()} {func.__name__} successfully")
                return result

            elif result is not False:
                logger.info(f"Domain {domain.name()} {func.__name__} successfully")
                return result if isinstance(result, bool) else True
            
            else:
                logger.error(f"Domain {domain.name()} {func.__name__} failed")
                return False

        except libvirt.libvirtError as e:
            logger.error(f"Domain operation failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return False

    return wrapper


def timeit(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        logger.info(f"{func.__name__} took {duration:.2f} seconds")
        return result

    return wrapper

@timeit
def run_cmd(
    cmd: Optional[str] = None,
    hostname: str = get_env_var("LIBVIRT_HOST"),
    username: str = get_env_var("LIBVIRT_USER")
) -> Union[Tuple[int, str, str], None]:
    """使用ssh远程执行命令

    Args:
        cmd (Optional[str], optional): 待执行命令
        hostname (str, optional): 远程主机
        username (str, optional): ssh用户名

    Returns:
        Union[TTuple[int, str, str], None]: 返回一个三元组
        - exit_status (int): 命令执行完毕后的返回状态
        - stdout (str): 执行命令后的标准输出
        - stderr (str): 执行命令后的标准错误输出
        若命令执行时出错，则返回None
    """
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(hostname=hostname, username=username)
        
        _, stdout, stderr = ssh.exec_command(cmd)
        exit_status = stdout.channel.recv_exit_status()
        
    except Exception as e:
       logger.error(f"Remote connect or command excute failed：{str(e)}")
       return None
   
    finally:
        ssh.close()
    
    return exit_status, stdout.read().decode(), stderr.read().decode()
