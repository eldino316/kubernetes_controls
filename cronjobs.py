from kubernetes import client, config

def get_cronjobs_in_namespace(namespace):
    batch_api = client.BatchV1Api()
    cronjobs = batch_api.list_namespaced_cron_job(namespace).items
    return cronjobs