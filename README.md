# vmware_ai_agent

## 一个简单的 VMware ai agent demo
![95aebd245d798e68fa1da8e0e2d0fc2](https://github.com/user-attachments/assets/3abc7d32-23bf-4c5c-9358-de5d8491ff77)

## 使用方法：

```bash
git clone https://github.com/RyrieNorth/vmware_ai_agent.git
pip install -r requirements.txt

python main.py
```

## 初始化 vmrest：

```bash
# 启用VMware rest API程序
%VMWarePath%/vmrest.exe -C
username: xxx
password: xxx

# 测试启动
vmrest.exe

# 建议使用提供的start_vmrest.bat批处理脚本以管理员模式启动
./start_vmrest.bat
```

## 配置文件详情：

```yaml
vmware:
  api_base: "http://localhost:8697/api" # VMware Workstation REST API 监听地址
  api_key: "" # 服务器认证密钥，需要base64加密，例如：admin:Aa123456! -> YWRtaW46QWExMjM0NTYhCg==

llm:
  api_base: "" # LLM API地址
  api_key: "" # LLM API密钥
  module: "Qwen3-30B-A3B" # LLM模型名称，经过测试，目前Qwen3系列的模型速度、响应均为上等
  lang: "zh" # prompts的类型
```


## 使用演示：
https://github.com/user-attachments/assets/1dd9664a-a874-48c5-8aa5-9e8f06741cd3

