from kubernetes import client

def get_ingresses_in_namespace(namespace):
    networking_v1 = client.NetworkingV1Api()
    ingresses = networking_v1.list_namespaced_ingress(namespace).items
    return ingresses