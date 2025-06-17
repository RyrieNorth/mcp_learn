import asyncio
import shutil
import time

from dotenv import load_dotenv

from utils.env_utils import get_env_var
from utils.logger import logger, set_log_file, set_log_format, set_log_level

from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, set_tracing_disabled
from openai.types.responses import ResponseTextDeltaEvent, ResponseStreamEvent
from openai import OpenAIError
from agents.mcp import MCPServerStreamableHttp
from agents.model_settings import ModelSettings

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter

load_dotenv()
set_tracing_disabled(disabled=True)

set_log_level("DEBUG")
set_log_file(file_name="agent_log.log")
set_log_format(format_type="text")

openai_client = AsyncOpenAI(
    api_key=get_env_var("API_KEY"),
    base_url=get_env_var("API_URL")
)

extra_body = {
    "chat_template_kwargs": {"enable_thinking": True},
}

# 全局保持历史
chat_history = []

async def run(agent: Agent, message: dict) -> ResponseStreamEvent:
    logger.debug(f"Running: {message}")
    start_time = time.time()
    result = Runner.run_streamed(starting_agent=agent, input=message)
    first_response = True

    async for event in result.stream_events():
        if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
            if first_response:
                first_response = False
                logger.info(f"⏱️ 首个响应耗时: {time.time() - start_time:.2f} 秒")
            print(event.data.delta, end="", flush=True)

    print()
    return result.final_output

async def main():
    global chat_history
    
    session = PromptSession()

    # 创建 MCP Streamable连接
    async with MCPServerStreamableHttp(
        name="Streamable HTTP Python Server",
        params={"url": "http://localhost:8000/mcp"},
        cache_tools_list=True
    ) as server:

        agent = Agent(
            name="Assistant",
            instructions=
"""
你是一名虚拟机智能管理助手，专注于帮助用户**查询和控制虚拟机与卷资源**。
你拥有一套丰富的工具来完成虚拟机管理相关任务，请根据用户的请求，**准确选择合适的工具**调用。

### 🔍 你的能力包括（但不限于）：
- 查询虚拟机的基本信息、IP、状态、资源占用（CPU、磁盘、网络等）
- 启动、关闭、暂停、重启、克隆、删除虚拟机
- 查询和管理存储池中的卷（列出卷、创建、克隆、删除、上传、下载等）
- 获取宿主机的总体资源状态和虚拟机统计信息

### 🧠 工具使用建议：
1. **尽量使用聚合工具**（如：`fetch_vm_full_stats`）来提高效率，避免多个独立查询；
2. **支持组合调用**多个工具解决复杂问题（如：同时查询状态和磁盘信息）；
3. 当用户的请求不涉及操作或数据查询（如问候语、确认、建议等），**不调用工具，直接回复即可**；
4. 如果用户只提到“虚拟机名”但未明确操作，你可以先查询基本状态（如`fetch_vm_state`）再推断意图；
5. 当你调用完工具后，请将**结果以 Markdown 表格形式返回**，并加简要说明；
6. 当结果为空或工具返回失败，请**明确告知用户原因**（如找不到虚拟机、操作失败等）；
7. 当用户说参数自定时，请先检查先前有没有使用相同的工具查询过类似的参数，如果有，请尽量**避免使用**。再者，在执行前可以使用相关工具先列出参数是否存在

### 📋 输出格式说明：
- 若调用了工具，优先以 Markdown 表格返回结果；
- 若无数据，输出：“未找到相关信息，请确认虚拟机/卷名称是否正确。”
- 若为简单问答类问题，如“你是谁”、“你好”等，请自然回答，并附加一句：
“我是虚拟机智能助手，请问我能为你做些什么？Ciallo～(∠・ω<)⌒★”

### 须知：
- 请不要说谎，请不要自作主张脑部数据，除非用户允许你根据工具内容生成相对应的函数；
- 请在有限的环境中尽可能完成用户的的请求，若遇到超出自身之外的问题，可以询问用户，直到问题完成；
- 请根据以上说明，合理调用工具并生成结果。
""",
            mcp_servers=[server],
            model=OpenAIChatCompletionsModel(
                model=get_env_var("LLM_MODEL"),
                openai_client=openai_client
            ),
            model_settings=ModelSettings(
                max_tokens=8192,
                temperature=0.6,
                top_p=0.9,
                truncation='auto',
                extra_body=extra_body,
                tool_choice='auto'
            ),
        )

        while True:
            try:
                completer = WordCompleter([
                    '你好，你是谁？',
                    '你能做什么？',
                    'What can you do ？',
                    '现在北京时间',
                    'What time is it in Beijing now.',
                    '当前有哪些虚拟机？',
                    'How many virtual machines are there on the host ?',
                    '当前正在运行的有哪些虚拟机？',
                    'Which virtual machines are currently running on the host ?',
                    '当前有哪些虚拟网络？',
                    'How many virtual networks are there on the host ?',
                    '当前有哪些虚拟网桥？',
                    'How many bridge interfaces are there on the host ?',
                    '当前有哪些存储池？',
                    'How many storage pools are there on the host ?',
                    '当前存储池中有多少卷？',
                    'How many volumes are there in the storage pool ?',
                    '使用"虚拟机名称"查询这个虚拟机信息：',
                    'Lookup this virtual machine by name: ',
                    '使用虚拟机"UUID"查询这个虚拟机信息：',
                    'Lookup this virtual machine by UUID: ',
                    'quit',
                    'exit'
                    ], 
                    ignore_case=True
                )
                user_input = await session.prompt_async("Input your questions (or 'exit/quit' to exit): >>> ", completer=completer)

                if not user_input:
                    continue

                if user_input in {"exit", "quit"}:
                    print("Bye!")
                    break

                messages = chat_history + [{"role": "user", "content": user_input}]

                message_output = await run(agent, messages)
                chat_history.append({"role": "assistant", "content": message_output})

            except OpenAIError:
                raise
            except KeyboardInterrupt:
                print("Exit.")
                break
            except EOFError:
                print("Exit.")
                break

if __name__ == "__main__":
    if not shutil.which("uv"):
        raise RuntimeError(
            "uv command is not installed, Please install it: https://docs.astral.sh/uv/getting-started/installation"
        )
    asyncio.run(main())
