from kubernetes import client
import subprocess


def get_service_in_namespace(namespace):
    core_api = client.CoreV1Api()
    service = core_api.list_namespaced_service(namespace).items
    return service

def get_service_details(namespace, service_name):
    try:
        command = ["kubectl", "describe", "svc", service_name, "-n", namespace]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        service_details = result.stdout
        return service_details
    except subprocess.CalledProcessError as e:
        return {"error": f"Erreur : {e.stderr}"}