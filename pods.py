from flask import Flask, render_template, request
from kubernetes import client, config
import json
import subprocess
import os

app = Flask(__name__)

try:
    config.load_kube_config()
except Exception as e:
    print(f"Erreur lors du chargement de la configuration Kubernetes : {str(e)}")

@app.route('/podt', methods=['GET', 'POST'])
def pods():
    # Récupérez le namespace sélectionné depuis la requête
    selected_namespace = request.args.get('namespace', 'default')  # Par défaut, utilisez 'default' si aucun namespace n'est spécifié

    # Récupérez la liste de tous les namespaces disponibles sur le cluster
    namespaces = get_available_namespaces()

    # Récupérez la liste de tous les pods dans le namespace sélectionné
    pods = get_pods_in_namespace(selected_namespace)

    return render_template('tpod.html', pods=pods, namespaces=namespaces, selected_namespace=selected_namespace)

def get_available_namespaces():
    v1 = client.CoreV1Api()
    namespaces = v1.list_namespace().items
    return [namespace.metadata.name for namespace in namespaces]

def get_pods_in_namespace(namespace):
    core_api = client.CoreV1Api()
    pods = core_api.list_namespaced_pod(namespace).items
    return pods


if __name__ == '__main__':
     app.run(debug=True, host='127.0.0.1', port=5000)