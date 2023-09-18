from flask import Flask, render_template, request, redirect, url_for, jsonify
from kubernetes import client, config, utils
import os
from datetime import datetime
import pytz
import psutil
import yaml
import subprocess
import tempfile
from flask_wtf import FlaskForm
from wtforms import FileField

app = Flask(__name__)

os.environ['KUBECONFIG'] = os.path.expandvars('%USERPROFILE%\\.kube\\config')
yaml_dir = os.path.expandvars('D:\\PROJET MEMOIRE\\maquette\\kubernetes\\temp_yaml')

# Chargez la configuration Kubernetes

# Créez un objet Kubernetes API
kube_api = client.CoreV1Api()
core_api = client.CoreV1Api()

try:
    config.load_kube_config()
except Exception as e:
    print(f"Erreur lors du chargement de la configuration Kubernetes : {str(e)}")

@app.route('/', methods=['GET'])
def index():
    try:
        config.load_kube_config()
        contexts, _ = config.list_kube_config_contexts()
        clusters = [context['name'] for context in contexts]
        return render_template('home.html', clusters=clusters)
    except Exception as e:
        return jsonify(error="il y erreur dans le chargement du kubeconfig")


@app.route('/connect', methods=['POST'])
def connect():
    selected_cluster = request.form.get('cluster')

    # Utilisez la configuration Kubernetes pour se connecter au cluster sélectionné
    try:
        config.load_kube_config(context=selected_cluster)
        os.environ['KUBECONFIG'] = config.KUBE_CONFIG_DEFAULT_LOCATION
        return redirect(url_for('home'))  # Rediriger vers la page de tableau de bord après la connexion
    except Exception as e:
        return f"Erreur de connexion au cluster : {str(e)}"
    
@app.route('/home')
def home():
    logs = get_logs()
    return render_template('admin.html', logs=logs)    

def get_logs():
    logs = []

    try:
        # Récupérez les événements (events) de tous les clusters
        events = kube_api.list_event_for_all_namespaces().items

        # Récupérez les informations sur tous les nœuds (nodes) de tous les clusters
        nodes = kube_api.list_node().items

        utc = pytz.timezone('UTC')

        # Parcourez les événements
        for event in events:
            timestamp_utc = event.metadata.creation_timestamp.astimezone(utc)
            log_entry = {
                'timestamp': timestamp_utc.strftime("%Y-%m-%d %H:%M:%S"),
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
                        'timestamp': timestamp_utc.strftime("%Y-%m-%d %H:%M:%S"),
                        'namespace': 'Node',
                        'pod_name': node_name,
                        'event_type': condition.type,
                        'message': condition.message,
                    }
                    logs.append(log_entry)

    except Exception as e:
        logs.append(f"Erreur lors de la récupération des logs : {str(e)}")

    return logs

def get_available_namespaces():
    v1 = client.CoreV1Api()
    namespaces = v1.list_namespace().items
    return [namespace.metadata.name for namespace in namespaces]

def get_pods_in_namespace(namespace):
    core_api = client.CoreV1Api()
    pods = core_api.list_namespaced_pod(namespace).items
    return pods

def get_configmap_in_namespace(namespace):
    core_api = client.CoreV1Api()
    configmap = core_api.list_namespaced_config_map(namespace).items
    return configmap

def get_service_in_namespace(namespace):
    core_api = client.CoreV1Api()
    service = core_api.list_namespaced_service(namespace).items
    return service

def get_deployments_in_namespace(namespace):
    apps_api = client.AppsV1Api()
    deployments = apps_api.list_namespaced_deployment(namespace).items
    return deployments

def get_ingresses_in_namespace(namespace):
    networking_v1 = client.NetworkingV1Api()
    ingresses = networking_v1.list_namespaced_ingress(namespace).items
    return ingresses

def get_persistent_volume_claims_in_namespace(namespace):
    core_api = client.CoreV1Api()
    pvc_list = core_api.list_namespaced_persistent_volume_claim(namespace).items
    return pvc_list

def apply_yaml(file_path):
    cmd = f'kubectl apply -f {file_path}'
    os.system(cmd)

class UploadForm(FlaskForm):
    file = FileField('Sélectionnez un fichier YAML')

@app.route('/cpu')
def get_cpu_usage():
    cpu_usage = psutil.cpu_percent(interval=1)
    return jsonify(cpu_usage=cpu_usage)

@app.route('/ram')
def get_ram_usage():
    ram = psutil.virtual_memory()
    ram_usage = ram.percent
    return jsonify(ram_usage=ram_usage)

@app.route('/disk')
def get_disk_usage():
    disk_usage = psutil.disk_usage('/')
    disk_data = {
        'total': disk_usage.total,
        'used': disk_usage.used,
        'free': disk_usage.free,
        'percent': disk_usage.percent,
    }

    return jsonify(disk_data)

@app.route('/network_traffic')
def get_network_traffic():
    network_stats = psutil.net_io_counters()
    data = {
        'bytes_sent': network_stats.bytes_sent,
        'bytes_recv': network_stats.bytes_recv
    }
    return jsonify(data)

@app.route('/pods', methods=['GET', 'POST'])
def pods():
        # Vérifiez si l'utilisateur est connecté en vérifiant la présence de la variable d'environnement KUBECONFIG
    pod_name = request.args.get('namespace', 'default')

    yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]

    namespaces = get_available_namespaces()
    # Récupérez la liste de tous les pods dans tous les namespaces
    pods = get_pods_in_namespace(pod_name)

    return render_template('pods.html', pods=pods, yaml_files=yaml_files, namespaces=namespaces)

@app.route('/deployment', methods=['GET', 'POST'])
def deployment():
    # Récupérez le nom du déploiement à partir des paramètres de requête s'il est spécifié
    deployment_name = request.args.get('namespace', 'default')

    yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]

    namespaces = get_available_namespaces()

    # Récupérez la liste de tous les déploiements dans tous les namespaces
    deployments = get_deployments_in_namespace(deployment_name)

    return render_template('deployment.html', deployments=deployments, yaml_files=yaml_files, namespaces=namespaces)

@app.route('/configmap', methods=['GET', 'POST'])
def configmap():
   
   ConfigMap_name = request.args.get('namespace', 'default')

   yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]

   namespaces = get_available_namespaces() 
    
   configmap_list = get_configmap_in_namespace(ConfigMap_name)

   return render_template('configmap.html', configmaps=configmap_list, yaml_files=yaml_files, namespaces=namespaces)


@app.route('/secret', methods=['GET', 'POST'])
def secret():

    secret_name = request.args.get('namespace', 'default')

    yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]

    namespaces = get_available_namespaces() 
        
    v1 = client.CoreV1Api()
       
    secret_list = v1.list_secret_for_all_namespaces().items

    if secret_name:
        filtered_secret = [secret for secret in secret_list if secret_name in secret.metadata.name]
    else:
        filtered_secret = secret_list

    return render_template('secret.html', secrets=filtered_secret, yaml_files=yaml_files)
    

@app.route('/service', methods=['GET', 'POST'])
def service():

    service_name = request.args.get('namespace', 'default')

    yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]

    namespaces = get_available_namespaces() 

    service_list = get_service_in_namespace(service_name)

    return render_template('service.html', services=service_list, yaml_files=yaml_files, namespaces=namespaces)

@app.route('/ingress', methods=['GET', 'POST'])
def ingress():

    ingress_name = request.args.get('namespace', 'default')

    yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]
    
    namespaces = get_available_namespaces()

    ingress_list = get_ingresses_in_namespace(ingress_name)
        
    return render_template('ingress.html', ingresses=ingress_list, yaml_files=yaml_files, namespaces=namespaces)

@app.route('/pvc', methods=['GET', 'POST'])
def pvc():
    # Récupérez le nom de l'espace de noms à partir des paramètres de requête s'il est spécifié
    pvc_name = request.args.get('namespace', 'default')

    yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]

    namespaces = get_available_namespaces()

    # Récupérez la liste des PVC dans l'espace de noms spécifié
    pvc_list = get_persistent_volume_claims_in_namespace(pvc_name)

    return render_template('pvc.html', pvc_list=pvc_list, yaml_files=yaml_files, namespaces=namespaces)

@app.route('/install', methods=['GET', 'POST'])
def upload_file():
    form = UploadForm()
    if form.validate_on_submit():
        file = form.file.data
        if file:
            # Créez le répertoire temporaire s'il n'existe pas
            temp_dir = 'temp'
            os.makedirs(temp_dir, exist_ok=True)

            # Générez un chemin de fichier unique en utilisant le nom du fichier original
            file_path = os.path.join(temp_dir, file.filename)

            # Sauvegardez le fichier YAML temporairement sur le serveur
            file.save(file_path)

            # Appliquez le fichier YAML
            apply_yaml(file_path)

            # Supprimez le fichier temporaire
            os.remove(file_path)

            return redirect(url_for('upload_file'))
    return render_template('upload.html', form=form)

@app.route('/delete_deployment', methods=['POST'])
def delete_deployment():
    namespace = request.form.get('namespace')
    name = request.form.get('name')

    # Créez une instance de l'API de déploiement
    k8s_apps_v1 = client.AppsV1Api()

    try:
        # Supprimez le déploiement en utilisant le namespace et le nom fournis
        delete_options = client.V1DeleteOptions()
        k8s_apps_v1.delete_namespaced_deployment(name, namespace, body=delete_options)

        # Redirigez l'utilisateur vers une page de confirmation ou une page de liste de déploiements mise à jour
        return redirect(url_for('deployment', success_message='Le déploiement a été supprimé avec succès.'))
    except client.rest.ApiException as e:
        # Gérez les erreurs, par exemple, en affichant un message d'erreur
        error_message = f"Erreur lors de la suppression du déploiement : {e.reason}"
        return redirect(url_for('deployment', error_message=error_message))

@app.route('/delete_pod', methods=['POST'])
def delete_pod():
    namespace = request.form.get('namespace')
    pod_name = request.form.get('name')

    # Créez une instance de l'API CoreV1
    core_api = client.CoreV1Api()

    try:
        # Supprimez le pod en utilisant le namespace et le nom fournis
        delete_options = client.V1DeleteOptions()
        core_api.delete_namespaced_pod(pod_name, namespace, body=delete_options)

        # Redirigez l'utilisateur vers une page de confirmation ou une page de liste de pods mise à jour
        return redirect(url_for('pods', success_message='Le pod a été supprimé avec succès.'))
    except client.rest.ApiException as e:
        # Gérez les erreurs, par exemple, en affichant un message d'erreur
        error_message = f"Erreur lors de la suppression du pod : {e.reason}"
        return redirect(url_for('pods', error_message=error_message))

@app.route('/logs/<namespace>/<pod_name>', methods=['GET'])
def logs(namespace, pod_name):
    logs = get_pod_logs(namespace, pod_name)
    # Vérifiez si la requête est une requête AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(logs=logs.splitlines())
    
    return render_template('pods.html', logs=logs)

def get_pod_logs(namespace, pod_name):
    try:
        # Utilisez l'API Kubernetes Python pour récupérer les logs du pod
        api_instance = client.CoreV1Api()
        logs = api_instance.read_namespaced_pod_log(
            name=pod_name, namespace=namespace)
        return logs
    except Exception as e:
        return str(e)




if __name__ == '__main__':
     app.run(debug=True, host='127.0.0.1', port=5000)