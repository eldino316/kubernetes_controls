from kubernetes import client
import subprocess


def get_available_namespaces():
    v1 = client.CoreV1Api()
    namespaces = v1.list_namespace().items
    return [namespace.metadata.name for namespace in namespaces]

def get_namespace():
    try:
        v1 = client.CoreV1Api()
        namespaces = v1.list_namespace().items
        return namespaces
    except subprocess.CalledProcessError as e:
        error_message = f"Erreur lors de l'exécution de kubectl : {e}"
        return error_message    