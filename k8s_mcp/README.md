# 安装server环境：
```bash
uv pip install fastapi
```

# 启动server:
```bash
source env.sh && uv run server.py
```

# 测试访问:
```bash
curl --no-buffer -X POST http://localhost:8000/chat -H "Content-Type: application/json" -d '{"prompt": "你好，你是谁？请简单介绍一下自己>_<"}';echo
```
