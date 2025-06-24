import yaml
from typing import Optional, Union, Dict, Any
from template import NoAliasDumper

def gen_sa_template(
    sa_name: str,
    labels: Optional[Dict[str, str]] = None,
    template_type: str = 'yaml'
) -> Union[str, Dict[str, Any]]:
    base = {
        "kind": "ServiceAccount",
        "apiVersion": "v1",
        "metadata": {
            "name": f"{sa_name}",
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
