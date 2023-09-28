from kubernetes import client
import subprocess


def get_deployments_in_namespace(namespace):
    apps_api = client.AppsV1Api()
    deployments = apps_api.list_namespaced_deployment(namespace).items
    return deployments

def get_deploy_details(namespace, deployment_name):
    try:
        command = ["kubectl", "describe", "deploy", deployment_name, "-n", namespace]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        deploy_details = result.stdout
        return deploy_details
    except subprocess.CalledProcessError as e:
        return {"error": f"Erreur : {e.stderr}"}