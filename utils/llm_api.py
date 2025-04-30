import re
from openai import OpenAI
from .load_configs import load_configs
from .load_prompts import load_prompts

config = load_configs()
openai_api_base = config["llm"]["api_base"]
openai_api_key = config["llm"]["api_key"]
llm_module = config["llm"]["module"]
prompts = load_prompts()


def clean_tags(text: str) -> str:
    """
    清除模型输出中的 \<think\> 标签及其内容。

    - 移除所有 \<think\>...\</think\> 包裹的内容
    - 移除所有孤立的 \<think\> 或 \</think\>

    Args:
        text (str): 待清洗文本

    Returns:
        str: 清洗后的文本
    """
    # 去除成对的 <think>...</think> 包含的内容
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    # 去除孤立的 <think> 或 </think> 标签
    text = re.sub(r"</?think>", "", text)
    return text.strip()


def get_openai_client():
    """获取 OpenAI 客户端对象。"""
    return OpenAI(api_key=openai_api_key, base_url=openai_api_base)


def call_llm(prompt: str, temperature: float = 0.3) -> str:
    """统一调用 LLM 模型接口。

    Args:
        prompt (str): 构造好的用户提示语。
        temperature (float): 控制输出多样性，默认为 0.3。

    Returns:
        str: 模型输出的内容，已清理标签。
    """
    client = get_openai_client()
    response = client.chat.completions.create(
        model=llm_module,
        temperature=temperature,
        messages=[{"role": "user", "content": prompt}],
    )
    return clean_tags(response.choices[0].message.content)


def extract_intent(user_input: str, vm_info_json: str) -> str:
    """根据用户输入与虚拟机信息提取操作意图。

    Args:
        user_input (str): 用户的自然语言输入。
        vm_info_json (str): 当前虚拟机的 JSON 信息。

    Returns:
        str: 提取的意图 JSON 字符串。
    """
    template = prompts["extract_intent"]["zh"]
    prompt = template.format(user_input=user_input, vm_info_json=vm_info_json)
    return call_llm(prompt, temperature=0.5)


def find_vm_id(vm_info_json: str, target_vm_name: str) -> str:
    """根据虚拟机信息和名称查找对应的虚拟机 ID。

    Args:
        vm_info_json (str): 当前虚拟机的 JSON 信息。
        target_vm_name (str): 目标虚拟机的名称。

    Returns:
        str: 查找到的虚拟机 ID。
    """
    template = prompts["find_vm_id"]["zh"]
    prompt = template.format(vm_info_json=vm_info_json, target_vm_name=target_vm_name)
    return call_llm(prompt)


def extract_vm_summary(vm_info_raw: str) -> str:
    """根据原始虚拟机信息提取摘要信息。

    Args:
        vm_info_raw (str): 原始虚拟机 JSON 文本。

    Returns:
        str: 提取的摘要信息。
    """
    template = prompts["extract_vm_summary"]["zh"]
    prompt = template.format(vm_info_raw=vm_info_raw)
    return call_llm(prompt)
