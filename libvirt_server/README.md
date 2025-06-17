## 创建venv：
```bash
uv venv
```

## 应用虚拟环境：
```bash
source .venv/bin/activate
```

## 安装ansible：
```bash
uv pip install ansible -i https://mirrors.ustc.edu.cn/pypi/simple
```

## 安装基础环境
```bash
ansible-playbook playbooks/setup_kvm.yaml
```

## 安装libvirt开发包:
```bash
yum config-manager --set-enabled crb
yum install epel-release
yum install libvirt-devel gcc
```

## 同步环境：
```bash
cd path/to/fetch_time
uv sync
```

## 配置.env文件：
```bash
API_KEY=""  // LLM API Key
API_URL="https://api.siliconflow.cn"    // LLM API Server

LLM_MODEL="Qwen/Qwen3-30B-A3B"  // LLM MODEL

DEBUG=false

LIBVIRT_SERVER = "qemu+ssh://root@192.168.85.10/system" // Libvirt Server, 默认为qemu:///system
LIBVIRT_HOST = "192.168.85.10"  // Libvirt Server 服务器IP
LIBVIRT_USER = "root"   // Libvirt Server 连接用户

LOG_LEVEL = "WARNING"
```

## 配置MCP Server与Libvirt Server免密：
```bash
ssh-keygen -t rsa -N "" -f /root/.ssh/id_rsa
ssh-copy-id -i /root/.ssh/id_rsa.pub root@192.168.85.10
```

## 命令行使用：
```bash
# 查看帮助
usage: cli.py [-h] {console,hostinfo,net,bridge,pool,vm,vol} ...

Libvirt CLI Tool

positional arguments:
  {console,hostinfo,net,bridge,pool,vm,vol}
    console             Attach to VM console
    hostinfo            Host related operations
    net                 Net related operations
    bridge              Bridge related operations
    pool                Storage pool related operations
    vm                  Virtual machine related operations
    vol                 Volumes related operations

options:
  -h, --help            show this help message and exit

# 连接console：
[root@localhost ~]# python cli.py console rocky9-by-cli-create
Escape character is ^] (CTRL+])

[root@test ~]#
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
![image](https://github.com/user-attachments/assets/ec94f51f-96ff-4a24-9ffe-b06d32956176)

## 工具一览表：
![image](https://github.com/user-attachments/assets/8538ea07-9a6c-400a-ae5f-6fa2a021afb3)

## 启用MCP服务器：
![image](https://github.com/user-attachments/assets/587ccf56-c7fb-4c8b-9606-cb1f5608d2de)

## 简单聊天测试：
![image](https://github.com/user-attachments/assets/68b81b69-a5a3-41b5-9eea-1084b28aacd3)

## 测试工具调用：
![image](https://github.com/user-attachments/assets/fc19cfe7-7f2c-429d-97ee-29d67d42d854)
![image](https://github.com/user-attachments/assets/9aa75395-96ad-47b3-a304-f87d6a6b67aa)
![image](https://github.com/user-attachments/assets/bbebca4a-8062-4669-8a26-156a617e6cb4)
![image](https://github.com/user-attachments/assets/231a4a92-83c9-416c-9812-1f2ec6db2143)
![image](https://github.com/user-attachments/assets/812004da-904d-4953-9842-6d46f47ab999)

