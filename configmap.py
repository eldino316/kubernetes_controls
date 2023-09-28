from kubernetes import client


def get_configmap_in_namespace(namespace):
    core_api = client.CoreV1Api()
    configmap = core_api.list_namespaced_config_map(namespace).items
    return configmap