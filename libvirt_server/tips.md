# 设定python路径，避免模块引用失败
PYTHONPATH=.

# 逻辑架构：

# .env：
```bash
用于存放libvirt连接服务器或对象的环境变量文件
```

## connect.py
```bash
用于获取libvirt连接对象
内置get_rw_connect和get_ro_connect两个连接对象
根据实际情况严格调用
```

## console.py
```bash
使用串口连接虚拟机
须知：虚拟机需要启用ttyS0虚拟串口才能连接
使用方式：console_connect(uuid="a24cca60-973a-4cce-9ea7-b5ab23fce0dd")
```

## details.py
```bash
存放虚拟机电源状态、磁盘状态、网络状态、存储池状态、卷状态预定义类型
```

## env_utils.py
```bash
读取环境变量，若环境变量不存在，则弹异常
使用方式: get_env_var("ENV_VALUE")
```

## host_manager.py
```bash
用于获取宿主机的节点信息
内置三个函数: get_host_cpu_info(), get_numa_memory_info(), get_host_full_info()
使用方式：get_host_cpu_info(), get_numa_memory_info(), get_host_full_info()
```

## logger.py
```bash
自定义日志配置
```

## net_manager.py
```bash
用于管理虚拟网络与网桥设备
管理虚拟网络：
使用方式: network = get_network(net_name="mynet") //获取虚拟网络对象
get_network_info(network): 返回虚拟网络序列化字典
list_networks(): 列出所有虚拟网络
list_interface(): 列出所有网络设备
create_network(net_name="mynet", br_name="virbr1", gateway="192.168.15.1", netmask="255.255.255.0", dhcp_start="192.168.15.2", dhcp_end="192.168.15.253"): 创建虚拟网络
delete_network(net_name="mynet"): 删除虚拟网络


管理网桥：
使用方式：bm = BridgeManager(run_cmd) //初始化对象
bm.create("br0"): 创建名为br0的网桥
bm.interface_operation("br0", ["ens37", "ens38"]): 将网络设备添加进网桥
bm.delete("br0"): 删除名为br0的网桥
```

## pool_manager.py
```bash
用于管理存储池
使用方式：
list_pools(): 列出所有存储池
get_pool(pool_name="opt"): 获取存储池对象
get_pool_info(pool): 获取存储池信息
create_pool(pool_type="dir", pool_name="test", pool_uuid=(uuid.uuid4()), pool_path="/data/images"): 创建存储池
delete_pool("test"): 删除存储池
```

## vm_info.py
```bash
用于获取虚拟机详细信息：
使用方式：get_vm_state(domain_name="rocky9", devices_type="['disk']")
devices_type有: disk,interface,graphics等
```

## vm_list.py
```bash
用于获取虚拟机的ID和列表
使用方式：list_doamins(only_running = True / False)
True仅获取运行中虚拟机，False获取全部虚拟机
注意：当虚拟机未运行时，id为-1
```

## vm_manager.py
```bash
用于管理虚拟机与获取虚拟机状态
使用方式：
get_domain(vm_name="test"): 获取虚拟机对象
start_domain(domain): 开启虚拟机
shutdown_domain(domain): 关闭虚拟机
destroy_domain(domain): 强制关机
pause_domain(domain): 挂起虚拟机
resume_domain(domain): 恢复虚拟机
reboot_domain(domain): 重启虚拟机
reset_domain(domain): 强制重启
send_ctrl_alt_del(domain): 发送crtl+alt+delete
undefine_domain(domain): 删除虚拟机
set_auto_start(domain, "on / off"): 设置虚拟机是否开机自启
set_domain_ram(domain, 2048): 设置虚拟机最大内存使用量, 单位（MB）
set_domain_vcpus(domain, 2): 设置虚拟机vcpu数量
domain_cputime(domain): 获取虚拟机 cpu time
domain_state(domain): 获取虚拟机状态
domain_netstats(domain): 获取虚拟机网络状态
domain_diskstats(domain): 获取虚拟机磁盘状态
domain_ipaddrs(domain): 获取虚拟机ip地址信息
get_domain_full_stats(domain): 获取虚拟机所有信息
```

## vol_manager.py
```bash
用于管理存储池中的卷
使用方式：
list_volumes("default"): 列出default存储池中的所有卷
create_volume(storage_pool="default", vol_name="ryrie", vol_unit="MB", vol_size=10, vol_path="/var/libvirt/images/ryrie.img"): 创建存储卷
clone_volume(storage_pool="default", src_vol_name="ryrie", clone_vol_name="ryrie-clone"): 克隆卷
delete_volume(storage_pool="default", vol_name="ryrie-clone"): 删除卷

transfer_volume_file(pool_name="opt", volume_name="test.qcow2", file_path="/tmp/backup.img", action="download"): 下载卷到本地
create_and_upload(pool_name="opt", vol_name="backup.img", vol_path="/opt/backup.img", local_path="/tmp/backup.img"): 创建并上传卷
```

## 启用 bash 补全
```bash
activate-global-python-argcomplete --user
source /root/.bash_completion

echo 'eval "$(register-python-argcomplete cli.py)"' >> /root/.bashrc
source /root/.bashrc
```