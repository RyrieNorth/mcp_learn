import asyncio
import sys
from utils.middleware import async_handle_user_input

if __name__ == "__main__":
    # 判断是否传参，否则进入交互循环
    if len(sys.argv) > 1:
        user_input = sys.argv[1]
        asyncio.run(async_handle_user_input(user_input))
    else:
        print("进入交互模式，输入 `exit 或 quit` 可退出")
        while True:
            try:
                user_input = input("请输入指令 >>> ").strip()
                if user_input.lower() in ("exit", "quit"):
                    break
                if user_input:
                    asyncio.run(async_handle_user_input(user_input))
            except KeyboardInterrupt:
                print("\n退出。")
                break
