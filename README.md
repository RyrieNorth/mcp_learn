# 一个记录个人MCP学习的历程

## 环境安装:
```bash
#安装uv：
curl -LsSf https://astral.sh/uv/install.sh | sh

# 创建虚拟环境：
uv venv k8s_venv --python 3.13.3

# 应用venv虚拟环境：
source k8s_venv/bin/activate

# 安装ansible、ansible-runner、openai、kubernetes、docker、mcp[cli]、httpx：
uv pip install ansible ansible-runner openai kubernetes docker mcp[cli] httpx json_repair
```
