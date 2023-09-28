from kubernetes import client, config
import subprocess

def get_secret_in_namespace(namespace):
    core_api = client.CoreV1Api()   
    secret = core_api.list_namespaced_secret(namespace).items
    return secret  

def get_secret_details(namespace, secret_name):
    try:
        command = ["kubectl", "describe", "secret", secret_name, "-n", namespace]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        secret_details = result.stdout
        return secret_details
    except subprocess.CalledProcessError as e:
        return {"error": f"Erreur : {e.stderr}"}