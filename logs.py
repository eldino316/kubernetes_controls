from flask import Flask, render_template
from kubernetes import client, config
import os

app = Flask(__name__)

# Chargez la configuration Kubernetes
try:
    config.load_kube_config()
except Exception as e:
    print(f"Erreur lors du chargement de la configuration Kubernetes : {str(e)}")

# Créez un objet Kubernetes API
kube_api = client.CoreV1Api()

@app.route('/')
def index():
    logs = get_logs()
    return render_template('logs.html', logs=logs)

def get_logs():
    logs = []

    try:
        # Récupérez les événements (events) de tous les clusters
        events = kube_api.list_event_for_all_namespaces().items

        # Récupérez les informations sur tous les nœuds (nodes) de tous les clusters
        nodes = kube_api.list_node().items

        # Parcourez les événements
        for event in events:
            log_entry = {
                'namespace': event.metadata.namespace,
                'pod_name': event.involved_object.name,
                'event_type': event.type,
                'message': event.message,
            }
            logs.append(log_entry)

        # Parcourez les nœuds pour récupérer les logs de nœuds
        for node in nodes:
            node_name = node.metadata.name
            node_logs = kube_api.read_node_status(node_name).status.conditions
            for condition in node_logs:
                if condition.type == 'OutOfMemory' or condition.type == 'OutOfDisk':
                    log_entry = {
                        'namespace': 'Node',
                        'pod_name': node_name,
                        'event_type': condition.type,
                        'message': condition.message,
                    }
                    logs.append(log_entry)

    except Exception as e:
        logs.append(f"Erreur lors de la récupération des logs : {str(e)}")

    return logs

if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
