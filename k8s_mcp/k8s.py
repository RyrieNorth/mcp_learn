from core import *
import time

config_path="/root/mcp_learn/kubernetes/.kube/config"

# print(namespace_list(config_path=config_path))
# print(namespace_detail(config_path=config_path, ns_name="kube-system"))
# print(create_namespace(config_path=config_path, ns_name="test"))
# print(create_namespace(config_path=config_path, ns_name="test", label='env=dev'))
# time.sleep(2)
# print(delete_namespace(config_path=config_path, ns_name="test"))
# print(service_list(config_path))
# print(service_detail(config_path=config_path, service_name="my-service3"))
# print(create_service(service_name="my-service", service_type="NodePort", namespace_name="default", selector={"app": "my-app"}, ports=[
#         {"name": "http", "port": 80, "targetPort": 8080, "nodePort": 30080},
#         {"name": "https", "port": 443, "targetPort": 8443, "nodePort": 30443}
#     ],
#     config_path=config_path
# )
# )

# print(create_service(service_name="my-service3", service_type=None, namespace_name=None, selector=None, ports=[
#         {"name": "http", "port": 80, "targetPort": 8080},
#     ],
#     config_path=config_path
# )
# )
# print(delete_service(service_name="my-service4", namespace_name="default", config_path=config_path))
# print(node_list(config_path))
# print(pod_list(config_path=config_path))
print(pod_detail(config_path=config_path, pod_name="nginx-test"))

# print(create_pod(pod_name="test",
#                  namespace_name="default",
#                  container_names=[{
#                      "name": "nginx", "image": "dockerhub.ryrie.cn/library/nginx:latest", 
#                      "ports": [{"containerPort": 80 }],
#                      }],
#                  labels='{}',
#                  config_path=config_path
#                  ))