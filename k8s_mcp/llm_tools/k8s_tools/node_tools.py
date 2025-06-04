from utils.tools_registry import register_tool
from core.node_manager import node_list
from llm_tools.k8s_tools.config import config_file

@register_tool(
    name="get_node_list",
    description="获取 Kubernetes 节点列表",
    parameters={"type": "object", "properties": {}, "required": []}
)
def get_node_list_tool():
    return {"nodes": node_list(config_path=config_file)}
