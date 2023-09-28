from kubernetes import client
import subprocess


def get_configmap_in_namespace(namespace):
    core_api = client.CoreV1Api()
    configmap = core_api.list_namespaced_config_map(namespace).items
    return configmap

def get_config_details(namespace, configMap_name):
    try:
        command = ["kubectl", "describe", "configmap", configMap_name, "-n", namespace]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        config_details = result.stdout
        return config_details
    except subprocess.CalledProcessError as e:
        return {"error": f"Erreur : {e.stderr}"}