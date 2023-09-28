from kubernetes import client


def get_available_namespaces():
    v1 = client.CoreV1Api()
    namespaces = v1.list_namespace().items
    return [namespace.metadata.name for namespace in namespaces]