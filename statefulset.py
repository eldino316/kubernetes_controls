import subprocess
from kubernetes import client

def get_statefulsets_in_namespace(namespace):
    apps_api = client.AppsV1Api()
    statefulsets = apps_api.list_namespaced_stateful_set(namespace).items
    return statefulsets

def get_statefullset_details(namespace, statefullset_name):
    try:
        command = ["kubectl", "describe", "statefulset", statefullset_name, "-n", namespace]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        statefullset_details = result.stdout
        return statefullset_details
    except subprocess.CalledProcessError as e:
        return {"error": f"Erreur : {e.stderr}"}