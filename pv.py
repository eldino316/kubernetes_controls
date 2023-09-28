import subprocess
from kubernetes import client


def get_persistent_volume_in_namespace(namespace):
    core_api = client.CoreV1Api()
    pv_list = core_api.list_persistent_volume().items
    return pv_list

def get_pv_details(namespace, pv_name):
    try:
        command = ["kubectl", "describe", "pv", pv_name, "-n", namespace]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        pv_details = result.stdout
        return pv_details
    except subprocess.CalledProcessError as e:
        return {"error": f"Erreur : {e.stderr}"}