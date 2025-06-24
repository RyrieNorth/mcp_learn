import yaml
from typing import Optional, Union, Dict, Any, List
from template import NoAliasDumper

def gen_deployment_template(
    name: str,
    labels: Optional[Dict[str, str]] = None,
    replicas: int = 1,
    containers: Optional[List[Dict[str, Any]]] = None,
    template_type: str = 'yaml'
) -> Union[str, Dict[str, Any]]:
    # 默认标签：以 app=name 命名
    default_labels = {"app": name}
    labels = labels or default_labels

    # 默认容器：nginx 示例
    default_containers = [{
        "name": "nginx",
        "image": "nginx:latest",
        "ports": [{"containerPort": 80}],
        "resources": {}
    }]
    containers = containers or default_containers

    deployment = {
        "apiVersion": "apps/v1",
        "kind": "Deployment",
        "metadata": {
            "name": name,
            "labels": labels
        },
        "spec": {
            "replicas": replicas,
            "selector": {
                "matchLabels": labels
            },
            "template": {
                "metadata": {
                    "labels": labels
                },
                "spec": {
                    "containers": containers
                }
            }
        }
    }

    if template_type.lower() == 'yaml':
        return yaml.dump(deployment, sort_keys=False, Dumper=NoAliasDumper)
    elif template_type.lower() == 'json':
        return deployment
    else:
        raise ValueError("template_type must be either 'yaml' or 'json'")
