import asyncio
import json
import httpx
from dotenv import load_dotenv
from utils.logger import logger
from utils.debug import is_debug_mode
from utils.env_utils import get_env_var
from openai.types.responses import ResponseTextDeltaEvent, ResponseContentPartDoneEvent
from agents import (
    Agent,
    Runner,
    function_tool,
    AsyncOpenAI,
    OpenAIChatCompletionsModel,
    ModelSettings,
    ItemHelpers,
    set_tracing_disabled
)
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter

# 加载环境变量
load_dotenv()
set_tracing_disabled(disabled=True)

# 初始化 OpenAI 客户端
openai_client = AsyncOpenAI(
    api_key=get_env_var("API_KEY"),
    base_url=get_env_var("API_URL")
)

extra_body = {
    "chat_template_kwargs": {"enable_thinking": False},
}

@function_tool
async def fetch_time(timezone: str = "Asia/Shanghai") -> str:
    """
    异步获取指定时区的当前时间信息。

    Args:
        timezone (str): 时区名称，例如 "Asia/Shanghai"

    Returns:
        str: 包含当前时间信息的 JSON 字符串，结构如下：
            {
                "year": int,              # 年份，例如 2025
                "month": int,             # 月份（1-12）
                "day": int,               # 日期（1-31）
                "hour": int,              # 小时（0-23）
                "minute": int,            # 分钟（0-59）
                "seconds": int,           # 秒数（0-59）
                "milliSeconds": int,      # 毫秒数
                "dateTime": str,          # ISO 格式完整时间，例如 "2025-06-06T14:28:40.1356805"
                "date": str,              # 格式化日期，例如 "06/06/2025"
                "time": str,              # 格式化时间，例如 "14:28"
                "timeZone": str,          # 时区名，例如 "Asia/Shanghai"
                "dayOfWeek": str,         # 星期几，例如 "Friday"
                "dstActive": bool         # 是否为夏令时，True/False
            }
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url="https://timeapi.io/api/time/current/zone",
            params={"timeZone": timezone}
        )
        response.raise_for_status()
        time_result = json.dumps(response.json(), ensure_ascii=False)
        return time_result


fetch_time_agent = Agent(
    name="Fetch Time",
    instructions="This is a tool to help get now time and day of week with external api",
    model=OpenAIChatCompletionsModel(
        model=get_env_var("LLM_MODEL"),
        openai_client=openai_client,
    ),
    model_settings=ModelSettings(
        max_tokens=8192,
        temperature=0.6,
        top_p=0.9,
        truncation="auto",
        extra_body=extra_body
    ),
    tools=[fetch_time]
)

chat_history = []

async def main():
    global chat_history
    session = PromptSession()
    while True:
        try:
            completer = WordCompleter(['现在北京时间', '北京时间', 'quit', 'exit'], ignore_case=True)
            user_input = await session.prompt_async("Input your questions (or 'exit/quit' to exit): >>> ", completer=completer)
            messages = chat_history + [{"role": "user", "content": user_input}]
            tool_name = ""
            tool_args = {}
            tool_output = {}
            message_output = ""


            if is_debug_mode():
                logger.debug("chat_messages: %s", messages)

            if not user_input:
                continue
            
            if user_input in {"exit", "quit"}:
                print("Bye!")
                break
            
            if user_input:
                result = Runner.run_streamed(
                    fetch_time_agent,
                    input=messages
                )

                logger.info("===== Run Starting =====")

                async for event in result.stream_events():
                    if event.type == "raw_response_event" and isinstance(event.data, ResponseTextDeltaEvent):
                        print(event.data.delta, end="", flush=True)

                    elif event.type == "raw_response_event" and isinstance(event.data, ResponseContentPartDoneEvent):
                        print()

                    elif event.type == "run_item_stream_event":
                        if event.item.type == "tool_call_item":
                            raw_item = getattr(event.item, "raw_item", None)
                            if raw_item:
                                tool_name = getattr(raw_item, "name", "Unknown tool.")
                                tool_args = getattr(raw_item, "arguments", "{}")

                                if isinstance(tool_args, str):
                                    try:
                                        tool_args = json.loads(tool_args)
                                    except json.JSONDecodeError:
                                        tool_args = {"raw_arguments": tool_args}

                        elif event.item.type == "tool_call_output_item":
                            tool_output = event.item.output

                        elif event.item.type == "message_output_item":
                            message_output = ItemHelpers.text_message_output(event.item)
            
            if is_debug_mode():
                if tool_name:
                    logger.debug("Calling tool name: %s", tool_name)
                    logger.debug("Calling tool arguments: %s", tool_args)
                    logger.debug("Tool output: %s", tool_output)
                    logger.debug("Message output: %s", message_output)

                logger.info("===== Run complete =====")
            
            

            chat_history.append({"role": "assistant", "content": message_output})
        
        except KeyboardInterrupt:
            print("Exit.")
            break
        
        except EOFError:
            print("Exit.")
            break

if __name__ == "__main__":
    asyncio.run(main())
