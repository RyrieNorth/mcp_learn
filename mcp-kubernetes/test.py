from utils.kubernetes_manager import KubernetesManager
import json

from pprint import pprint

from utils.logger import set_log_level

from template import *

set_log_level("DEBUG")

km = KubernetesManager()

if __name__ == "__main__":
    # print(km.get.get_pods("", all_namespace=True))
    # print(km.delete.delete_namespaces("test"))
    # print(km.describe.describe_nodes("k8s-master.ryrie.cn"))
    # print(km.describe.describe_namespaces("ryrie"))
    # print(km.describe.describe_services("", "True"))
    # print(km.describe.describe_deployments("ryrie"))
    # pprint(km.list.kubectl_get_api_resoucrs())
    # print(km.scale.kubectl_scale_resources("ryrie", "2", '', 'deployment'))
    # print(km.logs.kubectl_logs("deployment", "ryrie"))
    # print(km.portforward.start_port_forward("pods", "nginx", 8080, 80))
    # print(km.portforward.stop_port_forward(proc_id=13039))
    # print(gen_ns_template("test-ns", {"env": "dev"}, "json"))
    # ns_json = gen_ns_template("test-ns", {"env": "dev"}, "json")
    # print(json.dumps(ns_json, indent=2))
    # print(km.create.create_namespace(ns_name="test"))
#     custom_yaml = """
# apiVersion: v1
# kind: ConfigMap
# metadata:
#   name: my-config
#   namespace: test
# data:
#   key: value
# """
#     print(km.create.kubectl_create(manifest=custom_yaml))
    # print(gen_deployment_template("my-app", template_type="yaml"))
    # containers = [
    #     km.create.build_container("nginx", "dockerhub.ryrie.cn/library/nginx", ports=[80,8080])
    # ]
    # yaml = (gen_deployment_template(
    #     name="test-app",
    #     labels={"env": "dev"},
    #     replicas=2,
    #     containers=containers,
    #     template_type="yaml"
    # ))
    # print(yaml)
    # print(km.create.kubectl_create(manifest=yaml))


    # print(yaml_str)
    # print(km.delete.delete_pods("test-nginx"))
    # print(km.create.create_pod(
    #     pod_name="test-nginx",
    #     containers=[{
    #         "name": "nginx",
    #         "image": "dockerhub.ryrie.cn/library/nginx",
    #         "ports": [{"containerPort": 80}],
    #         "imagePullPolicy": "IfNotPresent"
    #     }]
    # ))
    # containers = [
    #     km.create.build_container("nginx", "dockerhub.ryrie.cn/library/nginx", ports=[80,8080])
    # ]
    # print(km.create.create_pod(
    #     pod_name="test-nginx-1",
    #     containers=containers
    # ))
    # yaml_output = gen_configmap_template(
    #     name="my-config",
    #     data={
    #         "APP_ENV": "production",
    #         "TIMEOUT": "30"
    #     },
    #     namespace="default"
    # )

    # print(yaml_output)
    # 创建 generic secret
    # print(km.create.create_secret(
    #     secret_type="generic",
    #     name="test-secret",
    #     namespace="default",
    #     data={"MYSQL_PASS": "beikong123"}
    # ))

    # 创建 TLS secret
    # print(km.create.create_secret(
    #     secret_type="tls",
    #     name="tls-cert",
    #     cert="/root/mcp_learn/kubernetes/certs/dockerhub.ryrie.cn.crt",
    #     key="/root/mcp_learn/kubernetes/certs/dockerhub.ryrie.cn.key"
    # ))

    # 创建 docker registry secret
    # print(km.create.create_secret(
    #     secret_type="docker-registry",
    #     name="docker-auth",
    #     docker_username="admin",
    #     docker_password="Aa123456!",
    #     docker_server="https://dockerhub.ryrie.cn"
    # ))
    # ports = [
    #     km.create.build_port("http", "TCP", port=80, targetPort=80, nodePort=30080),
    #     km.create.build_port("https", "TCP", port=443, targetPort=443, nodePort=30443)
    # ]
    # # # print(ports)
    # # yaml = (gen_service_template("myapp"))
    # yaml = (gen_service_template(
    #     name="myapp-nodeport",
    #     service_type="NodePort",
    #     ports=ports
    # ))
    # print(km.create.create_from_template(yaml))
