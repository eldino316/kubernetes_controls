from kubernetes import client, config


def get_secret_in_namespace(namespace):
    core_api = client.CoreV1Api()   
    secret = core_api.list_namespaced_secret(namespace).items
    return secret  