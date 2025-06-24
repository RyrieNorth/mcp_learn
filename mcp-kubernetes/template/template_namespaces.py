import yaml
from typing import Optional, Union, Dict, Any
from template import NoAliasDumper

def gen_ns_template(
    ns_name: str,
    labels: Optional[Dict[str, str]] = None,
    template_type: str = 'yaml'
) -> Union[str, Dict[str, Any]]:
    base = {
        "apiVersion": "v1",
        "kind": "Namespace",
        "metadata": {
            "name": ns_name
        }
    }

    if labels:
        base["metadata"]["labels"] = labels

    if template_type.lower() == 'yaml':
        return yaml.dump(base, sort_keys=False, Dumper=NoAliasDumper)
    elif template_type.lower() == 'json':
        return base
    else:
        raise ValueError("template_type must be either 'yaml' or 'json'")
