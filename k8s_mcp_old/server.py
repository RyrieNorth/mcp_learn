import uuid
import time
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import llm_tools # 保留原有 function 工具注册
from utils import *
import uvicorn

app = FastAPI()

# 全局对话历史记录：session_id -> [history]
session_store = {}

# 请求体模型
class ChatRequest(BaseModel):
    prompt: str
    session_id: str = None  # 可选，若为空则自动生成

# 系统提示词（固定）
system_prompt = {
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
async def chat_endpoint(req: ChatRequest):
    session_id = req.session_id or str(uuid.uuid4())

    # 初始化对话历史
    if session_id not in session_store:
        session_store[session_id] = [system_prompt]

    history = session_store[session_id]

    # 用户输入追加到历史
    history.append({"role": "user", "content": req.prompt})

    # 响应生成器
    def stream_response():
        try:
            for chunk in call_llm(prompt=req.prompt, thinking=True, max_tokens=8192, messages=history, temperature=0.1):
                yield chunk
                time.sleep(0.02)  # 控制逐字输出
        except Exception as e:
            yield f"[ERROR] {str(e)}"

    return StreamingResponse(stream_response(), media_type="text/plain", headers={"X-Session-ID": session_id})


if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=8000)
