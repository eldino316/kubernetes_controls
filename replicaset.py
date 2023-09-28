import subprocess
from kubernetes import client, config


def get_replicasets_in_namespace(namespace):
    config.load_kube_config()
    apps_api = client.AppsV1Api()  
    replicasets = apps_api.list_namespaced_replica_set(namespace).items
    return replicasets

def get_replicatset_details(namespace, replicaset_name):
    try:
        command = ["kubectl", "describe", "replicaset", replicaset_name, "-n", namespace]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        replicaset_details = result.stdout
        return replicaset_details
    except subprocess.CalledProcessError as e:
        return {"error": f"Erreur : {e.stderr}"}