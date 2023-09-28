from kubernetes import client

def get_service_in_namespace(namespace):
    core_api = client.CoreV1Api()
    service = core_api.list_namespaced_service(namespace).items
    return service