from kubernetes import client


def get_persistent_volume_claims_in_namespace(namespace):
    core_api = client.CoreV1Api()
    pvc_list = core_api.list_namespaced_persistent_volume_claim(namespace).items
    return pvc_list
