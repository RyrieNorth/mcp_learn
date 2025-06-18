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

# 命令行演示：
https://www.bilibili.com/video/BV11MT7zxE52

# 使用演示：
https://github.com/user-attachments/assets/1bbddb56-baef-4dc7-9ab4-cfc8adcf2d6c

# 会话记录演示：
```bash
curl --no-buffer -i -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "你好，你是谁？请简单介绍一下自己>_<"}';echo


curl --no-buffer -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"prompt": "除了这些，你还会什么？", "session_id": "01488276-a71a-46f9-a9a5-620a1094319d"}'
```
https://github.com/user-attachments/assets/2251ef5b-b7c0-423c-9546-a1130c416967

