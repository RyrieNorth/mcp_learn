import asyncio
import json
import time
from concurrent.futures import ThreadPoolExecutor
from .llm_api import extract_intent, extract_vm_summary, find_vm_id
from .vmware_api import get_vm_info, get_power_info, set_power
from .logger import logger

_vm_cache = {"timestamp": 0, "raw": "", "summary": ""}


def get_cached_vm_info(ttl=60):
    """
    获取缓存的虚拟机信息，若缓存过期则重新从 VMware API 获取

    该函数会检查缓存中虚拟机信息的时间戳，若超出 TTL（默认60秒），
    会重新从 VMware 获取虚拟机信息，并更新缓存。

    Args:
        ttl (int, optional): 缓存过期的时间，单位为秒，默认60秒。

    Returns:
        tuple:
            - raw (str): 原始虚拟机信息
            - summary (str): 经过摘要处理的虚拟机信息
    """
    now = time.time()
    if now - _vm_cache["timestamp"] > ttl:
        _vm_cache["raw"] = get_vm_info()
        _vm_cache["summary"] = extract_vm_summary(_vm_cache["raw"])
        _vm_cache["timestamp"] = now
    return _vm_cache["raw"], _vm_cache["summary"]


executor = ThreadPoolExecutor(max_workers=10)


def parse_intent(user_input: str, vm_info_raw: str):
    """
    解析用户输入的指令，识别意图并返回相关数据

    该函数接收用户的输入和原始虚拟机信息，提取虚拟机摘要并解析用户意图。
    如果解析后的意图数据是字符串格式，则转换为 JSON 格式；如果是字典格式，则直接返回。

    Args:
        user_input (str): 用户输入的指令，通常是关于虚拟机的操作请求。
        vm_info_raw (str): 原始虚拟机信息，用于生成虚拟机摘要。

    Returns:
        tuple:
            - intent_json (dict): 解析后的意图数据，包含虚拟机的操作类型和目标虚拟机信息。
            - vm_summary (str): 虚拟机的摘要信息，用于进一步分析。

    Raises:
        TypeError: 如果意图数据的类型既不是字符串也不是字典，将抛出该异常。
    """
    vm_summary = extract_vm_summary(vm_info_raw)
    intent_data = extract_intent(user_input, vm_summary)

    if isinstance(intent_data, str):
        intent_json = json.loads(intent_data)
    elif isinstance(intent_data, dict):
        intent_json = intent_data
    else:
        raise TypeError("意图数据类型不正确")

    return intent_json, vm_summary


# ----------- 包装为异步任务 -------------
async def async_find_vm_id(vm_summary, vm_name):
    """
    异步查找虚拟机 ID

    使用线程池执行 `find_vm_id`，通过虚拟机摘要和虚拟机名称查找虚拟机 ID。

    Args:
        vm_summary (str): 虚拟机信息摘要
        vm_name (str): 虚拟机名称

    Returns:
        str: 虚拟机 ID 或未找到的提示信息
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, find_vm_id, vm_summary, vm_name)


async def async_get_power_info(vm_id):
    """
    异步获取虚拟机的电源状态信息

    使用线程池执行 `get_power_info`，通过虚拟机 ID 获取电源状态。

    Args:
        vm_id (str): 虚拟机 ID

    Returns:
        dict: 包含虚拟机电源状态的字典，例如 `{"power_state": "poweredOn"}`。
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, get_power_info, vm_id)


async def async_set_power(vm_id, op):
    """
    异步设置虚拟机的电源状态

    使用线程池执行 `set_power`，通过虚拟机 ID 和操作指令设置电源状态。

    Args:
        vm_id (str): 虚拟机 ID
        op (str): 操作类型，"on" 启动虚拟机，"off" 关闭虚拟机。

    Returns:
        None
    """
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(executor, set_power, vm_id, op)


# ----------- 主逻辑异步处理 -------------
async def async_handle_user_input(user_input: str):
    """
    异步处理用户输入并执行虚拟机控制操作

    根据用户输入的指令，解析意图并进行相应的虚拟机操作，
    如查看虚拟机状态、启动或关闭虚拟机等。所有操作都将异步执行。

    Args:
        user_input (str): 用户输入的自然语言指令

    Returns:
        None
    """
    start_time = time.time()
    logger.info(f"接收到用户输入指令：{user_input}")

    # 获取缓存的虚拟机信息
    vm_info_raw, vm_summary = get_cached_vm_info()

    try:
        intent_json, vm_summary = parse_intent(user_input, vm_info_raw)
        vm_names = intent_json["vm_names"]
        intent = intent_json["intent"]
    except Exception as e:
        logger.error(f"解析意图失败: {e}")
        return

    logger.info(f"识别意图：操作={intent}，目标虚拟机={vm_names}")

    # 异步查找虚拟机 ID
    find_tasks = [async_find_vm_id(vm_summary, name) for name in vm_names]
    find_results = await asyncio.gather(*find_tasks)

    op_tasks = []
    for vm_name, vm_id_result in zip(vm_names, find_results):
        if "未找到" in vm_id_result:
            logger.error(f"未找到虚拟机：{vm_name}")
            continue

        for vm_id in vm_id_result.strip().splitlines():
            vm_id = vm_id.strip()
            logger.info(f"正在处理虚拟机 ID: {vm_id}")

            # 处理虚拟机操作
            async def handle_one(vm_name, vm_id):
                power_info = await async_get_power_info(vm_id)
                power_state = power_info.get("power_state", "unknown")

                match intent:
                    case "status":
                        logger.info(f"虚拟机 {vm_name} 当前状态：{power_state}")
                    case "start":
                        if power_state == "poweredOn":
                            logger.info(f"虚拟机 {vm_name} 已经在运行中。")
                        else:
                            logger.info(f"正在启动虚拟机 {vm_name}...")
                            await async_set_power(vm_id, "on")
                            logger.info(f"虚拟机 {vm_name} 启动成功。")
                    case "stop":
                        if power_state == "poweredOff":
                            logger.info(f"虚拟机 {vm_name} 已处于关机状态。")
                        else:
                            logger.info(f"正在关闭虚拟机 {vm_name}...")
                            await async_set_power(vm_id, "off")
                            logger.info(f"虚拟机 {vm_name} 关闭成功。")
                    case _:
                        logger.error(f"未识别的操作类型：{intent}")

            op_tasks.append(handle_one(vm_name, vm_id))

    # 等待所有操作完成
    await asyncio.gather(*op_tasks)

    elapsed = time.time() - start_time
    logger.info(f"本次指令处理完毕，用时：{elapsed:.2f} 秒")
