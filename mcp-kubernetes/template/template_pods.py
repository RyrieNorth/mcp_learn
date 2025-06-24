import yaml
from typing import Optional, Union, Dict, Any, List
from template import NoAliasDumper

def gen_pod_template(
    name: str,
    labels: Optional[Dict[str, str]] = None,
    containers: Optional[List[Dict[str, Any]]] = None,
    template_type: str = 'yaml'
) -> Union[str, Dict[str, Any]]:
    # 默认标签
    default_labels = {"app": name}
    labels = labels or default_labels

    # 默认容器
    default_containers = [{
        "name": name,
        "image": "nginx:latest",
        "ports": [{"containerPort": 80}],
        "resources": {},
        "imagePullPolicy": "IfNotPresent"
    }]
    containers = containers or default_containers

    pod = {
        "apiVersion": "v1",
        "kind": "Pod",
        "metadata": {
            "name": name,
            "labels": labels
        },
        "spec": {
            "containers": containers
        }
    }

    if template_type.lower() == 'yaml':
        return yaml.dump(pod, sort_keys=False, Dumper=NoAliasDumper)
    elif template_type.lower() == 'json':
        return pod
    else:
        raise ValueError("template_type must be either 'yaml' or 'json'")
