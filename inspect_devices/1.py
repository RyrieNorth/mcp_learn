import ansible_runner

inventory = """
[h3c] 
ansible_host=192.168.1.254 ansible_ssh_user: "admin" ansible_ssh_pass: "admin" ansible_network_os: community.network.ce
"""

r = ansible_runner.run(
    private_data_dir='.',  # 当前目录
    playbook='dis_version.yaml',
    inventory=inventory,
    host_pattern="h3c",
    
    
    extravars={
        'ansible_ssh_user': 'admin',
        'ansible_ssh_pass': 'admin',
        'ansible_network_os': 'community.network.ce'
    }
)

# print("Status:", r.status)      # e.g. "successful"
# print("RC:", r.rc)              # e.g. 0
# print("Stdout:")
print(r.stdout.read())          # 全部输出

# 如果你想取结果对象
for each_host_event in r.events:
    if each_host_event.get("event") == "runner_on_ok":
        result = each_host_event.get("event_data", {}).get("res", {})
        if 'stdout' in result:
            print("纯净stdout：")
            print("\n".join(result['stdout']))

