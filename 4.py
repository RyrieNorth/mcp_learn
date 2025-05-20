from openai import OpenAI
import subprocess
import json

# API配置
api_key = ""
api_base = ""
llm_module = "Qwen3-30B-A3B"


# 创建客户端
client = OpenAI(api_key=api_key, base_url=api_base)

# 定义工具
tools = [
    {
        "type": "function",
        "function": {
            "name": "inspect_hardware_info",
            "description": "巡检网络设备硬件信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_name": {
                        "type": "string",
                        "description": "设备的名称，例如 core_switch/192.168.1.254/核心交换机",
                    }
                },
                "required": ["device_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_interface_info",
            "description": "巡检网络设备接口信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_name": {
                        "type": "string",
                        "description": "设备的名称，例如 core_switch/192.168.1.254/核心交换机",
                    }
                },
                "required": ["device_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_security_info",
            "description": "巡检网络设备基本安全信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_name": {
                        "type": "string",
                        "description": "设备的名称，例如 core_switch/192.168.1.254/核心交换机",
                    }
                },
                "required": ["device_name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "inspect_other_info",
            "description": "巡检网络设备其他信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_name": {
                        "type": "string",
                        "description": "设备的名称，例如 core_switch/192.168.1.254/核心交换机",
                    }
                },
                "required": ["device_name"],
            },
        },
    },
]

# 额外参数配置
extra_body = {
    "chat_template_kwargs": {"enable_thinking": False},
}

if __name__ == "__main__":
    print("进入交互模式，输入 `exit 或 quit` 可退出")
    while True:
        try:
            user_input = input("请输入指令 >>> ").strip()
            if user_input.lower() in ("exit", "quit"):
                break
            if user_input:
                prompt = user_input
        except KeyboardInterrupt:
            print("\n退出。")
            break

        # 设定提示词
        messages = [
            {
                "role": "system",
                "content": (
                    "你是一位网络设备运维专家，擅长处理H3C和华为设备的自动化巡检任务。"
                    "请直接输出巡检分析报告，内容要结构清晰、结论明确，避免使用以下内容："
                    "1）“如需进一步检查...”"
                    "2）“请提供...”"
                    "3）“如果你想...”"
                    "4）任何形式的建议性尾句。"
                    "5) 以markdown的形式输出。"
                    "请假设已有所有必要数据，不要引导用户提供更多信息。"
                )
            },
            {"role": "user", "content": prompt}
        ]

        # 步骤1: 发送初始请求，让模型决定是否使用工具
        print("步骤1: 发送初始请求...")
        response = client.chat.completions.create(
            model=llm_module,
            temperature=0.6,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            stream=False,
            extra_body=extra_body,
        )

        # 获取模型响应
        assistant_message = response.choices[0].message
        print(f"\n模型响应: {assistant_message}")

        # 步骤2: 检查是否有工具调用
        if hasattr(assistant_message, "tool_calls") and assistant_message.tool_calls:
            print("\n步骤2: 发现工具调用")

            # 将助手消息添加到历史中
            assistant_msg_dict = {
                "role": "assistant",
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                    for tool_call in assistant_message.tool_calls
                ],
            }

            # 如果内容不为None，添加content字段
            if assistant_message.content is not None:
                assistant_msg_dict["content"] = assistant_message.content

            messages.append(assistant_msg_dict)
            print(f"\n添加到消息历史的助手消息: {assistant_msg_dict}")

            # 处理每个工具调用
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)

                print(f"\n调用工具: {function_name}")
                print(f"\n工具参数: {function_args}")

                # 直接工具获取结果
                if function_name == "inspect_hardware_info":
                    try:
                        print("\n尝试手动调用工具获取数据...")
                        # 调用工具获取信息
                        tool_result = subprocess.run(["uv", "run", "inspetion_hardware_info.py"], capture_output=True, text=True)
                        print(f"\n工具返回的时间数据: {tool_result}")

                        # 将工具结果格式化为易于理解的字符串
                        formatted_result = json.dumps(
                            tool_result.stdout, ensure_ascii=False, indent=2
                        )
                    except Exception as e:
                        print(f"工具调用失败: {e}")
                        formatted_result = json.dumps(
                            {"error": f"Failed to invoke cmd: {str(e)}"}
                        )
                        
                elif function_name == "inspect_interface_info":
                    try:
                        print("\n尝试手动调用工具获取数据...")
                        # 调用工具获取信息
                        tool_result = subprocess.run(["uv", "run", "inspetion_interface_info.py"], capture_output=True, text=True)
                        print(f"\n工具返回的时间数据: {tool_result}")

                        # 将工具结果格式化为易于理解的字符串
                        formatted_result = json.dumps(
                            tool_result.stdout, ensure_ascii=False, indent=2
                        )
                    except Exception as e:
                        print(f"工具调用失败: {e}")
                        formatted_result = json.dumps(
                            {"error": f"Failed to invoke cmd: {str(e)}"}
                        )
                        
                elif function_name == "inspect_security_info":
                    try:
                        print("\n尝试手动调用工具获取数据...")
                        # 调用工具获取信息
                        tool_result = subprocess.run(["uv", "run", "inspetion_security_info.py"], capture_output=True, text=True)
                        print(f"\n工具返回的时间数据: {tool_result}")

                        # 将工具结果格式化为易于理解的字符串
                        formatted_result = json.dumps(
                            tool_result.stdout, ensure_ascii=False, indent=2
                        )
                    except Exception as e:
                        print(f"工具调用失败: {e}")
                        formatted_result = json.dumps(
                            {"error": f"Failed to invoke cmd: {str(e)}"}
                        )

                elif function_name == "inspect_other_info":
                    try:
                        print("\n尝试手动调用工具获取数据...")
                        # 调用工具获取信息
                        tool_result = subprocess.run(["uv", "run", "inspetion_other_info.py"], capture_output=True, text=True)
                        print(f"\n工具返回的时间数据: {tool_result}")

                        # 将工具结果格式化为易于理解的字符串
                        formatted_result = json.dumps(
                            tool_result.stdout, ensure_ascii=False, indent=2
                        )
                    except Exception as e:
                        print(f"工具调用失败: {e}")
                        formatted_result = json.dumps(
                            {"error": f"Failed to invoke cmd: {str(e)}"}
                        )

                else:
                    formatted_result = ""

                # 添加工具结果到消息历史
                tool_message = {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": function_name,
                    "content": formatted_result,
                }
                messages.append(tool_message)
                print(f"\n添加到消息历史的工具结果: {tool_message}")

            # 打印完整的消息历史，用于调试
            print("\n完整的消息历史:")
            for i, msg in enumerate(messages):
                print(f"消息 {i}: {msg}")

            # 步骤3: 发送第二次请求，包含工具结果
            print("\n步骤3: 发送第二次请求，包含工具调用结果...")
            # 在请求之前稍微等待一下，确保工具执行完成
            # time.sleep(1)

            second_response = client.chat.completions.create(
                model=llm_module,
                temperature=0.6,
                messages=messages,
                stream=False,
                extra_body={"chat_template_kwargs": {"enable_thinking": False}},
            )

            final_message = second_response.choices[0].message
            text = final_message.content
            print("\n最终模型回复:")
            print(final_message.content)

            # 保存为 Markdown 原文
            # if function_name == "inspect_hardware_info":
            #     with open("core_switch_hardware_report.md", "w", encoding="utf-8") as f:
            #         f.write(text.strip())
            # elif function_name == "inspect_interface_info":
            #     with open("core_switch_interface_report.md", "w", encoding="utf-8") as f:
            #         f.write(text.strip())
            # else:
            with open("core_switch_report.md", "w", encoding="utf-8") as f:
                f.write(text.strip())

            print("\n巡检报告已生成！请查看当前路径:")
        else:
            # 如果模型没有请求使用工具
            print("\n模型直接回复(未使用工具):")
            print(assistant_message.content)

