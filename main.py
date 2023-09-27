from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_socketio import SocketIO
from kubernetes import client, config, utils
import os
import requests
from datetime import datetime
import pytz
import psutil
import yaml
import subprocess
import tempfile
from flask_wtf import FlaskForm
from wtforms import FileField, TextAreaField


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
socketio = SocketIO(app)

os.environ['KUBECONFIG'] = os.path.expandvars('%USERPROFILE%\\.kube\\config')
yaml_dir = os.path.expandvars('D:\\PROJET MEMOIRE\\maquette\\kubernetes\\temp_yaml')
kubernetes_api_url = "http://localhost:8001"

temp_yaml_dir = 'temp_yaml'

# Assurez-vous que le répertoire temporaire existe
os.makedirs(temp_yaml_dir, exist_ok=True)

# Chargez la configuration Kubernetes

# Créez un objet Kubernetes API
kube_api = client.CoreV1Api()
core_api = client.CoreV1Api()

try:
    config.load_kube_config()
except Exception as e:
    print(f"Erreur lors du chargement de la configuration Kubernetes : {str(e)}")


def start_minikube_proxy():
    try:
        subprocess.Popen(["minikube", "kubectl", "proxy"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, start_new_session=True)
        print("La commande minikube kubectl proxy a été lancée en arrière-plan.")
    except Exception as e:
        print(f"Une erreur s'est produite : {str(e)}")

start_minikube_proxy()

@app.route('/', methods=['GET'])
def index():
    try:
        config.load_kube_config()
        contexts, _ = config.list_kube_config_contexts()
        clusters = [context['name'] for context in contexts]
        return render_template('home.html', clusters=clusters)
    except Exception as e:
        return jsonify(error="il y erreur dans le chargement du kubeconfig")
    
@socketio.on('connect')
def handle_connect():
    print('Client connected')

@socketio.on('disconnect')
def handle_disconnect():
    print('Client disconnected')    
    
@socketio.on('user_input')
def handle_user_input(input):
    commands = input.split('\n')
    for command in commands:
        try:
            result = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, text=True)
            socketio.emit('terminal_output', result)
        except subprocess.CalledProcessError as e:
            socketio.emit('terminal_output', e.output)    

@app.route('/open_pod_shell/<pod_name>')
def open_pod_shell(pod_name):
    # Exécutez la commande kubectl exec pour ouvrir un shell interactif sur le pod
    command = f'kubectl exec -it {pod_name} -- /bin/bash'
    
    try:
        subprocess.run(command, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        return f"Erreur lors de l'ouverture du shell : {e}"

    return "Shell ouvert avec succès"

@app.route('/execute_command', methods=['POST'])
def execute_command():
    data = request.get_json()
    command = data['command']
    pod_name = data['podName']

    # Exécutez la commande dans le pod Kubernetes
    try:
        result = subprocess.check_output(f'kubectl exec -it {pod_name} -- {command}', shell=True, stderr=subprocess.STDOUT, text=True)
        return jsonify(result)
    except subprocess.CalledProcessError as e:
        return jsonify(e.output)

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
        response = requests.get(f"{kubernetes_api_url}/api/v1/events")
        events = response.json()['items']

        # Récupérez les informations sur tous les nœuds (nodes) de tous les clusters
        response = requests.get(f"{kubernetes_api_url}/api/v1/nodes")
        nodes = response.json()['items']

        utc = pytz.timezone('UTC')

        # Parcourez les événements
        for event in events:
            timestamp_utc = datetime.strptime(event['metadata']['creationTimestamp'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc)
            log_entry = {
                'timestamp': timestamp_utc.strftime("%Y-%m-%d %H:%M:%S"),
                'namespace': event['metadata']['namespace'],
                'pod_name': event['involvedObject']['name'],
                'event_type': event['type'],
                'message': event['message'],
            }
            logs.append(log_entry)

        # Parcourez les nœuds pour récupérer les logs de nœuds
        for node in nodes:
            node_name = node['metadata']['name']
            node_conditions = node['status']['conditions']
            for condition in node_conditions:
                if condition['type'] in ('OutOfMemory', 'OutOfDisk'):
                    timestamp_utc = datetime.strptime(condition['lastTransitionTime'], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc)
                    log_entry = {
                        'timestamp': timestamp_utc.strftime("%Y-%m-%d %H:%M:%S"),
                        'namespace': 'Node',
                        'pod_name': node_name,
                        'event_type': condition['type'],
                        'message': condition['message'],
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

def get_persistent_volume_in_namespace(namespace):
    core_api = client.CoreV1Api()
    pv_list = core_api.list_persistent_volume(namespace).items
    return pv_list

def get_statefulsets_in_namespace(namespace):
    apps_api = client.AppsV1Api()
    statefulsets = apps_api.list_namespaced_stateful_set(namespace).items
    return statefulsets

def get_replicasets_in_namespace(namespace):
    config.load_kube_config()
    apps_api = client.AppsV1Api()  
    replicasets = apps_api.list_namespaced_replica_set(namespace).items
    return replicasets

def get_jobs_in_namespace(namespace):
    config.load_kube_config()
    batch_api = client.BatchV1Api()
    jobs = batch_api.list_namespaced_job(namespace).items
    return jobs

def get_cronjobs_in_namespace(namespace):
    batch_api = client.BatchV1Api()
    cronjobs = batch_api.list_namespaced_cron_job(namespace).items
    return cronjobs

def get_secret_in_namespace(namespace):
    core_api = client.CoreV1Api()   
    secret = core_api.list_namespaced_secret(namespace).items
    return secret   

def apply_yaml(file_path):
    try:
        cmd = f'kubectl apply -f {file_path}'
        os.system(cmd)
        flash(f'Fichier YAML "{file_path.filename}" installé avec succès dans le cluster.', 'success')
    except subprocess.CalledProcessError as e:
        flash(f'Erreur lors de l\'installation du fichier YAML : {str(e)}', 'error')    
    
    

class UploadForm(FlaskForm):
    yaml_file = FileField('Importer un fichier YAML', render_kw={"class": "custom-file-input"})
    yaml_code = TextAreaField('Éditer le YAML', render_kw={"class": "form-control"})
    yaml_template = TextAreaField('Modèle de YAML', render_kw={"class": "form-control"})

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

@app.route('/network_data')
def network_data():
    # Collecter les données sur le réseau à l'aide de psutil
    network_info = psutil.net_io_counters(pernic=True)
    interfaces = list(network_info.keys())
    data = [network_info[iface] for iface in interfaces]

    # Préparer les données pour le graphique Chart.js
    labels = interfaces
    interface_values = [d.bytes_sent + d.bytes_recv for d in data]

    # Collecter les informations sur la bande passante réseau
    network_bandwidth = psutil.net_if_stats()

    # Préparer les données pour le graphique Chart.js pour la bande passante
    bandwidth_labels = interfaces
    bandwidth_values = [network_bandwidth[iface].speed for iface in interfaces]

    # Créer un dictionnaire JSON pour les données du graphique
    chart_data = {
        'labels': labels,
        'interface_values': interface_values,
        'bandwidth_labels': bandwidth_labels,
        'bandwidth_values': bandwidth_values,
    }

    return jsonify(chart_data)

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
           
    secrets = get_secret_in_namespace(secret_name)

    return render_template('secret.html', secrets=secrets, yaml_files=yaml_files, namespaces=namespaces)
    

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
    pvc_name = request.args.get('namespace', 'default')

    yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]

    namespaces = get_available_namespaces()

    pvc_list = get_persistent_volume_claims_in_namespace(pvc_name)

    return render_template('pvc.html', pvc_list=pvc_list, yaml_files=yaml_files, namespaces=namespaces)

@app.route('/pv', methods=['GET', 'POST'])
def pv():
    pv_name = request.args.get('namespace', 'default')

    yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]

    namespaces = get_available_namespaces()

    pv_list = get_persistent_volume_claims_in_namespace(pv_name)

    return render_template('pv.html', pv_list=pv_list, yaml_files=yaml_files, namespaces=namespaces)

@app.route('/statefullset', methods=['GET', 'POST'])
def statefullset():
    statefullset_name = request.args.get('namespace', 'default')

    yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]

    namespaces = get_available_namespaces()

    statefullset_list = get_statefulsets_in_namespace(statefullset_name)

    return render_template('statefullset.html', statefullset_list=statefullset_list, yaml_files=yaml_files, namespaces=namespaces)

@app.route('/replicatset', methods=['GET', 'POST'])
def replicatset():
    replicatset_name = request.args.get('namespace', 'default')

    yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]

    namespaces = get_available_namespaces()

    replicatset_list = get_replicasets_in_namespace(replicatset_name)

    return render_template('replicatset.html', replicatset_list=replicatset_list, yaml_files=yaml_files, namespaces=namespaces)

@app.route('/jobs', methods=['GET', 'POST'])
def jobs():
    jobs_name = request.args.get('namespace', 'default')

    yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]

    namespaces = get_available_namespaces()

    jobs_list = get_jobs_in_namespace(jobs_name)

    return render_template('jobs.html', jobs_listt=jobs_list, yaml_files=yaml_files, namespaces=namespaces)

@app.route('/cronjobs', methods=['GET', 'POST'])
def cronjobs():
    cronjobs_name = request.args.get('namespace', 'default')

    yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]

    namespaces = get_available_namespaces()

    cronjobs_list = get_cronjobs_in_namespace(cronjobs_name)

    return render_template('cronjobs.html', cronjobs_listt=cronjobs_list, yaml_files=yaml_files, namespaces=namespaces)


def check_if_resource_exists(resource_type, resource_name):
    try:
        # Exécutez la commande kubectl get pour vérifier si l'objet existe
        get_command = f'kubectl get {resource_type} {resource_name} -o name'
        subprocess.check_output(get_command, shell=True)
        return True
    except subprocess.CalledProcessError:
        return False

def install_yaml(file_path):
    try:
        # Utilisez kubectl apply pour installer l'objet YAML
        install_command = f'kubectl apply -f {file_path}'
        subprocess.run(install_command, shell=True, check=True)
        return True, None  # Installation réussie
    except subprocess.CalledProcessError as e:
        return False, str(e)  

@app.route('/install', methods=['GET', 'POST'])
def install():
    if request.method == 'POST':
        file = request.files['yaml_file']
        resource_type = request.form.get('resource_type')  # Obtenez le type de ressource sélectionné
        if file and resource_type:
            # Enregistrez le fichier YAML dans le répertoire temporaire
            file_path = os.path.join(temp_yaml_dir, file.filename)
            file.save(file_path)

            # Obtenez le nom de l'objet YAML à partir du chemin du fichier
            yaml_object_name = os.path.basename(file_path)

            # Vérifiez si l'objet YAML existe déjà dans le cluster
            if check_if_resource_exists(resource_type, yaml_object_name):
                message = f'L\'objet YAML "{yaml_object_name}" existe déjà dans le cluster.'
                return jsonify({'error': message})

            # Installez le fichier YAML en utilisant kubectl
            success, error_message = install_yaml(file_path)

            # Supprimez le fichier temporaire
            os.remove(file_path)

            if success:
                message = f'Fichier YAML "{yaml_object_name}" installé avec succès dans le cluster.'
                return jsonify({'success': message})
            else:
                message = f'Erreur lors de l\'installation du fichier YAML : {error_message}'
                return jsonify({'error': message})
            
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
    
@app.route('/yaml/<resource_type>/<namespace>/<resource_name>', methods=['GET'])
def get_resource_yaml(resource_type, namespace, resource_name):
    try:
        # Utilisez l'API Kubernetes Python pour récupérer le YAML du resource
        api_instance = client.CustomObjectsApi()
        
        if resource_type == 'pod':
            group = 'v1'
            version = 'v1'
            plural = 'pods'
        elif resource_type == 'deployment':
            group = 'apps'
            version = 'v1'
            plural = 'deployments'
        elif resource_type == 'service':
            group = ''
            version = 'v1'
            plural = 'services'
        else:
            return "Type de ressource non pris en charge"

        resource = api_instance.get_namespaced_custom_object(
            group, version, namespace, plural, resource_name)
        
        # Convertissez le dictionnaire YAML en chaîne YAML
        yaml_string = yaml.dump(resource, default_flow_style=False)

        # Renvoyez la chaîne YAML à votre modèle HTML pour affichage
        return render_template('pods', yaml_string=yaml_string)
    except Exception as e:
        return str(e)



if __name__ == '__main__':
    socketio.run(app, debug=True)