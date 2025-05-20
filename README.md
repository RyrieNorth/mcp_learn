```bash
核心技术：
用户输入 --> 发送到 OpenAI ChatCompletion API
                ↓
         function_call 被触发
                ↓
        Python 执行本地命令 (subprocess)
                ↓
            获取输出，返回给用户
```

https://github.com/user-attachments/assets/824c3f53-31f6-498f-97f0-60eb02795d8c

