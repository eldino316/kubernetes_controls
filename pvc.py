import subprocess
from kubernetes import client


def get_persistent_volume_claims_in_namespace(namespace):
    core_api = client.CoreV1Api()
    pvc_list = core_api.list_namespaced_persistent_volume_claim(namespace).items
    return pvc_list

def get_pvc_details(namespace, pvc_name):
    try:
        command = ["kubectl", "describe", "pvc", pvc_name, "-n", namespace]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        pvc_details = result.stdout
        return pvc_details
    except subprocess.CalledProcessError as e:
        return {"error": f"Erreur : {e.stderr}"}