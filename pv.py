from kubernetes import client


def get_persistent_volume_in_namespace(namespace):
    core_api = client.CoreV1Api()
    pv_list = core_api.list_persistent_volume(namespace).items
    return pv_list