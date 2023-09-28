from kubernetes import client

def get_statefulsets_in_namespace(namespace):
    apps_api = client.AppsV1Api()
    statefulsets = apps_api.list_namespaced_stateful_set(namespace).items
    return statefulsets