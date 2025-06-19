import time
import functools

from typing import Callable, Any

from utils.logger import logger

def timeit(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start
        logger.info(f"{func.__name__} took {duration:.2f} seconds")
        return result

    return wrapper

def handle_kube_error(func: Callable[..., Any]) -> Callable[..., Any]:
    """统一处理 Kubernetes 操作的异常并记录日志"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            resource_name = None
            for key in ('resource_type', 'node_name', 'namespace', 'service', 'pod_name', 'app_name'):
                if key in kwargs and kwargs[key]:
                    resource_name = kwargs[key]
                    break

            resource_label = f"{func.__name__}({resource_name})" if resource_name else func.__name__

            result = func(*args, **kwargs)

            if result not in (False, None):
                logger.info(f"Kubernetes operation {resource_label} succeeded")
                return result
            else:
                logger.error(f"Kubernetes operation {resource_label} failed")
                return False

        except Exception as e:
            logger.error(f"Kubernetes operation {func.__name__} exception: {e}")
            return False

    return wrapper