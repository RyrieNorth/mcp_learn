## 创建venv：
```bash
uv venv
```

## 应用虚拟环境：
```bash
source .venv/bin/activate
```

## 安装kubectl命令行工具:
```bash
yum install -y kubectl
```

## 同步环境：
```bash
cd path/to/mcp-kubernetes
uv sync
```

## 配置.env文件：
```bash
KUBECONFIG="" // k8s凭据文件

API_KEY=""  // LLM API Key
API_URL="https://api.siliconflow.cn"    // LLM API Server

LLM_MODEL="Qwen/Qwen3-30B-A3B"  // LLM MODEL

DEBUG=false

LOG_LEVEL = "WARNING"
```

## 启动MCP Server：
```bash
uv run server.py
```

## 命令行使用：
```bash
uv run main.py
```

## 客户端对接：
![image](https://github.com/user-attachments/assets/36ec70d6-c5be-4fb1-8e4e-627dd37c134c)
![image](https://github.com/user-attachments/assets/bb5d5e32-b8cf-4776-b76d-5669025b2a5c)
![image](https://github.com/user-attachments/assets/efb93059-f8ab-4513-bb25-d3df3dd65644)

## 工具一览表：
![image](https://github.com/user-attachments/assets/1501a240-c43a-4451-a497-b39b75a07e24)

## 启用MCP服务器：
![image](https://github.com/user-attachments/assets/d0e7a35f-d86c-403b-be57-a40b7811b158)

## 简单聊天测试：
![image](https://github.com/user-attachments/assets/1f10ed1b-21dc-4a97-9f7d-b01e97400b02)

## 测试工具调用：

### 获取集群节点：
![image](https://github.com/user-attachments/assets/152fa7a9-7e9d-4eb6-b237-0d5d19598553)

### 创建命名空间：
![image](https://github.com/user-attachments/assets/1d30474c-c617-4276-9406-b9dca39560d3)

### 创建Pod：
![image](https://github.com/user-attachments/assets/a8cba3c2-d852-4f51-99c2-cfef3a6b6b43)
![image](https://github.com/user-attachments/assets/418afbd5-76e7-4185-bf9c-670d2e38fe0b)
![image](https://github.com/user-attachments/assets/4ea518fc-35fb-4b04-99c8-adceefab6e23)

### 创建端口转发：
![image](https://github.com/user-attachments/assets/1d1e8356-64b4-422c-b133-d4e9deeb9d45)
![image](https://github.com/user-attachments/assets/e62a2dbd-804a-46a9-847c-f3cb2cdba5c5)
![image](https://github.com/user-attachments/assets/3300540a-d9ba-44c5-b169-14f002700571)

### 创建deployment：
![image](https://github.com/user-attachments/assets/f890bec4-8a71-4ec1-baee-80e711e18ba8)
![image](https://github.com/user-attachments/assets/610e919d-20cf-4111-91fc-286513e308fd)
![image](https://github.com/user-attachments/assets/7467b86f-a74a-4923-ac65-8f3d65d77d49)



