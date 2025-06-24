from utils.resources_get_v1 import ResouecesGet
from utils.resources_delete_v1 import ResourcesDelete
from utils.resources_describe_v1 import ResouecesDescribe
from utils.resources_list_v1 import ResourceList
from utils.resources_scale_v1 import ResourceScale
from utils.resources_logs_v1 import ResourceLog
from utils.resources_patch_v1 import ResourcePatch
from utils.resources_create_v1 import ResourceCreate
from utils.resources_apply_v1 import ResourceApply

from utils.port_forward import PortForwarder
from utils.env_utils import get_env_var


class KubernetesManager:
    def __init__(self):
        self.env = get_env_var("KUBECONFIG")
        
        self.get = ResouecesGet(self.env)
        self.delete = ResourcesDelete(self.env)
        self.describe = ResouecesDescribe(self.env)
        self.list = ResourceList(self.env)
        self.scale = ResourceScale(self.env)
        self.logs = ResourceLog(self.env)
        self.patch = ResourcePatch(self.env)
        self.create = ResourceCreate(self.env)
        self.apply = ResourceApply(self.env)
        self.portforward = PortForwarder(self.env)