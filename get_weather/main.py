import sys
import json
import httpx
from logger import set_log_file, set_log_level, logger
from typing import Dict
from mcp.server.fastmcp import FastMCP

set_log_level("INFO")
set_log_file("server.log")

# 初始化mcp服务器：
host = "0.0.0.0"
port = "8000"
mcp = FastMCP(
    "Get Weather Server", host=host, port=port, log_level="INFO", log_requests=True
)
logger.info(f"MCP服务器 '{mcp.name}' 初始化成功！\n服务器地址: {host}:{port}")


# 注册MCP工具列表
@mcp.tool()
def get_weather(district_id: int) -> Dict:
    """基于区县的行政区划编码进行天气查询

    Args:
        district_id (int): 行政区划编码，例如海南省海口市海口区编码为：460100

    Returns:
        Dict: 信息列表
    """
    weather_server = "https://api.map.baidu.com/weather/v1/"
    ak = ""
    params = {
        "district_id": district_id,
        "data_type": "all",
        "ak": ak,
    }
    client = httpx.Client()
    try:
        response = client.get(url=weather_server, params=params)
        response.raise_for_status()
        if response:
            return response.json()
    except Exception as e:
        logger.error(f"无法查询天气信息: {e}")
        return str(e)


# 工具注册计数
tool_count = 0
for tool in mcp._tool_manager.list_tools():
    logger.info(f"已注册工具: {tool.name}")
    tool_count += 1

logger.info(f"总计注册MCP工具数量: {tool_count}")

# 启动MCP服务器
if __name__ == "__main__":
    try:
        mcp.run(transport="streamable-http")
    except KeyboardInterrupt:
        logger.info(f"Closing Fetch Time Server...")
        sys.exit(0)
