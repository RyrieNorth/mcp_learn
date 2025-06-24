import subprocess

from typing import Optional

from utils.logger import logger
from utils.functions import timeit, handle_kube_error

class ResourceApply:
    def __init__(self, env: Optional[str]) -> None:
        self.env = env