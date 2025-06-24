import kr8s
from utils.env_utils import get_env_var

get_env_var("KUBECONFIG")

# for pod in kr8s.get("pods", namespace=kr8s.ALL):
#     print(
#         pod.status.podIP,
#         pod.metadata.namespace,
#         pod.metadata.name,
#         pod.metadata.labels,
#         pod.status.hostIP,
#         pod.status.phase
#     )

# for node in kr8s.get("nodes"):
#     print(
#         node.metadata.name,
#         node.spec.podCIDR,
#     )

from kr8s.objects import Pod

pod = Pod.get("nginx")
pf = pod.portforward(remote_port=80, local_port=8080, address="0.0.0.0")

# Your other code goes here
pf.start()

# # Optionally stop the port forward thread (it will exit with Python anyway)
# pf.stop()