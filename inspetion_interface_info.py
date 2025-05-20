import ansible_runner
import contextlib
import os

with open(os.devnull, 'w') as fnull:
    with contextlib.redirect_stdout(fnull):
        r = ansible_runner.run(
            private_data_dir='.',
            playbook='inspetion_interface_info.yaml',
            extravars={
                'ansible_ssh_user': 'admin',
                'ansible_ssh_pass': 'admin',
                'ansible_network_os': 'community.network.ce'
            },
        )

for each_host_event in r.events:
    if each_host_event.get("event") == "runner_on_ok":
        host = each_host_event.get("event_data", {}).get("host", "unknown")
        result = each_host_event.get("event_data", {}).get("res", {})
        if 'stdout' in result:
            print(f"[{host}] 返回内容：")
            # 清洗输出：只保留非空行，strip去空格
            cleaned_lines = [line.strip() for line in result['stdout'] if line.strip()]
            print("\n".join(cleaned_lines))
