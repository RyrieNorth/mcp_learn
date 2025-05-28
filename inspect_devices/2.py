import ansible_runner
def run_playbook(playbook_name, hosts, username, password):
    # 工作目錄
    data_dir = "./"
    # 设置环境变量
    envvars = {
        "ANSIBLE_FORKS": 1,
    }

    # 运行 Ansible playbook 异步
    thread,runner = ansible_runner.run_async(
        private_data_dir=data_dir,
        playbook=playbook_name,
        quiet=True,
        envvars=envvars
    )


    # 处理并打印事件日志
    try:
        for event in runner.events:
            if 'stdout' in event and event['stdout']:
                print(event['stdout'])
    except Exception as e:
        raise Exception(f"Playbook execution failed: {str(e)}")

    # 等待线程完成
    thread.join()

    # 检查最终状态
    if runner.rc != 0:
        raise Exception(f"Playbook execution failed: {runner.rc}")

# 示例主机列表
hosts = ["h3c"]
username = 'admin'
password = 'admin'

playbook_path="./dis_version.yaml"

# 运行 playbook 并打印日志
try:
    run_playbook(playbook_path, hosts, username, password)
except Exception as e:
    print(f"Error: {e}")


