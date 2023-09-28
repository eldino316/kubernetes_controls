import subprocess
from kubernetes import client

def get_ingresses_in_namespace(namespace):
    networking_v1 = client.NetworkingV1Api()
    ingresses = networking_v1.list_namespaced_ingress(namespace).items
    return ingresses


def get_ingress_details(namespace, ingress_name):
    try:
        command = ["kubectl", "describe", "ingress", ingress_name, "-n", namespace]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        ingress_details = result.stdout
        return ingress_details
    except subprocess.CalledProcessError as e:
        return {"error": f"Erreur : {e.stderr}"}