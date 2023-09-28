from kubernetes import client, config


def get_replicasets_in_namespace(namespace):
    config.load_kube_config()
    apps_api = client.AppsV1Api()  
    replicasets = apps_api.list_namespaced_replica_set(namespace).items
    return replicasets