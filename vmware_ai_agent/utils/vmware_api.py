import requests
from .load_configs import load_configs
from .logger import logger

config = load_configs()
vm_api_base = config["vmware"]["api_base"]
vm_api_key = config["vmware"]["api_key"]


# === 接口请求函数 ===
def vmware_request(
    method: str,
    endpoint: str,
    data: str = None,
) -> dict:
    """
    通用的 VMware API 请求方法。

    Args:
        method (str): 请求方法，如 "GET"、"PUT"。
        endpoint (str): 请求路径（不包含 base URL），例如 "/vms"。
        data (str, optional): 请求体数据，通常用于 PUT 请求。

    Returns:
        dict: 响应的 JSON 数据。

    Raises:
        requests.RequestException: 请求异常时抛出。
    """
    url = f"{vm_api_base}{endpoint}"
    headers = {
        "Accept": "application/vnd.vmware.vmw.rest-v1+json",
        "Authorization": f"Basic {vm_api_key}",
    }
    if method.upper() == "PUT" or "POST":
        headers["Content-Type"] = "application/vnd.vmware.vmw.rest-v1+json"

    try:
        response = requests.request(method, url, headers=headers, data=data)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"请求失败 [{method} {url}]: {e}")
        return {}


# === VM Management ===
def get_vm_info() -> list[dict]:
    """获取所有虚拟机的基本信息。"""
    return vmware_request("GET", "/vms")


def get_vmsetup_info(vm_id: str) -> list[dict]:
    """获取虚拟机配置信息。"""
    return vmware_request("GET", f"/vms/{vm_id}")


def get_vmip_info(vm_id: str) -> list[dict]:
    """获取虚拟机IP地址信息。"""
    return vmware_request("GET", f"/vms/{vm_id}/ip")


# === VM Power Management ===
def get_power_info(vm_id: str) -> dict:
    """获取指定虚拟机的电源状态信息。"""
    return vmware_request("GET", f"/vms/{vm_id}/power")


def set_power(vm_id: str, state: str) -> dict:
    """设置指定虚拟机的电源状态。"""
    return vmware_request("PUT", f"/vms/{vm_id}/power", data=state)


# === VM Network Adapters Management ===
def get_vmnet_info() -> list[dict]:
    """获取所有vmnet的基本信息。"""
    return vmware_request("GET", "/vmnet")
