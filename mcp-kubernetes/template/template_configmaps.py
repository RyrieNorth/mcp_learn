import yaml
from typing import Optional, Dict, Union, Any
from template import NoAliasDumper

def gen_configmap_template(
    name: str,
    data: Dict[str, str],
    namespace: Optional[str] = None,
    template_type: str = "yaml"
) -> Union[str, Dict[str, Any]]:
    configmap = {
        "apiVersion": "v1",
        "kind": "ConfigMap",
        "metadata": {
            "name": name,
        },
        "data": data
    }

    if namespace:
        configmap["metadata"]["namespace"] = namespace

    if template_type.lower() == "yaml":
        return yaml.dump(configmap, sort_keys=False, Dumper=NoAliasDumper)
    elif template_type.lower() == "json":
        return configmap
    else:
        raise ValueError("template_type must be either 'yaml' or 'json'")
