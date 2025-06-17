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
