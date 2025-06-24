import yaml
from typing import Optional, Union, Dict, Any, List
from template import NoAliasDumper

def gen_service_template(
    name: str,
    labels: Optional[Dict[str, str]] = None,
    selector: Optional[Dict[str, str]] = None,
    ports: Optional[List[Dict[str, Any]]] = None,
    service_type: str = "ClusterIP",
    template_type: str = 'yaml'
) -> Union[str, Dict[str, Any]]:
    # 默认标签
    default_labels = {"app": name}
    labels = labels or default_labels
    selector = selector or labels

    # 默认端口
    default_ports = [{
        "port": 80,
        "targetPort": 80,
        "protocol": "TCP"
    }]
    ports = ports or default_ports

    service = {
        "apiVersion": "v1",
        "kind": "Service",
        "metadata": {
            "name": name,
            "labels": labels
        },
        "spec": {
            "type": service_type,
            "selector": selector,
            "ports": ports
        }
    }

    if template_type.lower() == 'yaml':
        return yaml.dump(service, sort_keys=False, Dumper=NoAliasDumper)
    elif template_type.lower() == 'json':
        return service
    else:
        raise ValueError("template_type must be either 'yaml' or 'json'")
