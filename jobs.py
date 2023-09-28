from kubernetes import config, client

def get_jobs_in_namespace(namespace):
    config.load_kube_config()
    batch_api = client.BatchV1Api()
    jobs = batch_api.list_namespaced_job(namespace).items
    return jobs