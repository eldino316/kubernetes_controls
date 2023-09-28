from kubernetes import client



def get_deployments_in_namespace(namespace):
    apps_api = client.AppsV1Api()
    deployments = apps_api.list_namespaced_deployment(namespace).items
    return deployments