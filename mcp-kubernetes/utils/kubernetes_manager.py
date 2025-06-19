from utils.resources_get import ResouecesGet
from utils.resources_delete import ResourcesDelete
from utils.env_utils import get_env_var

from typing import Optional, Any

class KubernetesManager:
    def __init__(self):
        self.env = get_env_var("KUBECONFIG")
        
        self.get = ResouecesGet(self.env)
        self.delete = ResourcesDelete(self.env)
    