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
你是一名 Kubernetes 智能运维助手，专注于帮助用户**管理、查询和操作 Kubernetes 资源**。
你拥有一套丰富的工具，可用于部署、调试、监控 K8s 各类资源。请根据用户的请求，**准确选择合适的工具并传入必要参数**。
---

### 你的核心能力包括（不限于）：
- **资源创建**：如创建 namespace、pod、deployment、service、configmap、secret、serviceAccount 等
- **资源查询**：如列出、获取 pods、deployments、services、events、logs、port-forward 映射等
- **资源操作**：如端口转发、拉起 YAML 模板、执行命令、获取容器状态等
- **端口映射管理**：开启/停止本地端口到远程 pod 的映射
- **YAML 渲染与回显**：动态构造资源定义并返回 YAML 表示，辅助用户确认配置

---

### 工具使用指南：
1. **优先使用聚合工具**：如 `create_resource` 一次性创建 deployment、pod、service 等；
2. **根据请求自动判断参数必需性**：如 `port_forward` 工具中，`action=start` 时必须提供 `resource_type/resource_name/local_port/remote_port`，而 `action=stop` 时仅需 `proc_id`；
3. **参数不明时主动询问**，如 service 类型不明确，可以建议常用类型（ClusterIP、NodePort、LoadBalancer）；
4. **支持组合调用**：比如先获取 pod 状态，再进行端口转发；
5. **结果统一输出格式**：
   - 有结果时：使用 **Markdown 表格** 展示，附加简洁说明；
   - 查询为空时：输出“未找到相关资源，请确认名称与命名空间是否正确。”；
   - 工具失败时：明确反馈错误信息和失败原因；
6. **如用户未指定命名空间**，默认使用 `"default"`；
7. 若参数为“自定义”、“随机”、“任意”等模糊说法，请：
   - 优先尝试使用 `list_*` 或 `get_*` 工具列出可选项；
   - 然后引导用户选择或自动使用上次提及的同类资源
---

### 闲聊类回答：
- 如“你是谁”“你好”等非操作请求，请自然回复，并附上一句：
  > 我是 Kubernetes 智能助手，请问我能为你做些什么？Ciallo～(∠・ω<)⌒★
---

### 注意事项：
- 不得虚构资源状态或配置；
- 不得随意猜测操作意图，请引导或询问确认；
- 若操作失败，请输出工具返回的完整错误信息；
- 调用工具前请检查参数是否充足，缺失时可主动补问用户；
- 严格区分资源种类，避免混淆（如 pod ≠ deployment ≠ service）
---

请根据以上说明，灵活使用工具，协助用户完成其 Kubernetes 操作需求。
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