from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
import llm_tools # 保留原有 function 工具注册
from utils import *
import uvicorn

app = FastAPI()

# 初始化 history
SYSTEM_MESSAGE = {
    "role": "system",
    "content": (
        "You are a Kubernetes assistant. "
        "You have many tools to help you manage Kubernetes resources. "
        "Not use markdown output. "
        "Not use english answer. "
        "Friendly use table output. "
        "Every response end with: Ciallo～(∠・ω<)⌒★"
    )
}


@app.post("/chat")
async def chat_endpoint(request: Request):
    body = await request.json()
    prompt = body.get("prompt", "")

    history = [
        {
            "role": "system",
            "content": (
                "You are a Kubernetes assistant. "
                "You have many tools to help you manage Kubernetes resources. "
                "Not use markdown output. "
                "Not use english answer. "
                "Friendly use table output. "
                "Every response end with: Ciallo～(∠・ω<)⌒★"
            )
        },
    ]

    # 定义生成器函数，逐步返回 token
    def llm_stream():
        try:
            for chunk in call_llm(prompt=prompt, thinking=True, max_tokens=8192, messages=history, temperature=0.1):
                yield chunk  # 一次只输出一个 token 或一个段落
        except Exception as e:
            yield f"[ERROR] {str(e)}"

    return StreamingResponse(llm_stream(), media_type="text/plain")

if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000)
