from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, Markup
from flask_socketio import SocketIO
from kubernetes import client, config, utils
import os
import psutil
import yaml
import subprocess
from pods import *
from nodes import *
from config import *
from cluster import *
from deploiment import *
from configmap import *
from namespace import *
from service import *
from ingress import *
from pvc import *
from pv import *
from statefulset import *
from replicaset import *
from jobs import *
from cronjobs import *
from secret import *


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
socketio = SocketIO(app)


                                           #route index de l'application

@app.route('/', methods=['GET'])
def index():
    try:
        config.load_kube_config()
        contexts, _ = config.list_kube_config_contexts()
        clusters = [context['name'] for context in contexts]
        return render_template('home.html', clusters=clusters)
    except Exception as e:
        return jsonify(error="il y erreur dans le chargement du kubeconfig")
    
@app.route('/home')
def home():
    logs = get_logs()
    return render_template('admin.html', logs=logs)

@app.route('/connect', methods=['POST'])
def connect():
    selected_cluster = request.form.get('cluster')
    try:
        config.load_kube_config(context=selected_cluster)
        os.environ['KUBECONFIG'] = config.KUBE_CONFIG_DEFAULT_LOCATION
        return redirect(url_for('home'))
    except Exception as e:
        return f"Erreur de connexion au cluster : {str(e)}"

                                         #lancement du socket pour le terminale       

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

                                        #route pour le monitoring

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
    network_info = psutil.net_io_counters(pernic=True)
    interfaces = list(network_info.keys())
    data = [network_info[iface] for iface in interfaces]
    labels = interfaces
    interface_values = [d.bytes_sent + d.bytes_recv for d in data]
    network_bandwidth = psutil.net_if_stats()
    bandwidth_labels = interfaces
    bandwidth_values = [network_bandwidth[iface].speed for iface in interfaces]
    chart_data = {
        'labels': labels,
        'interface_values': interface_values,
        'bandwidth_labels': bandwidth_labels,
        'bandwidth_values': bandwidth_values,
    }
    return jsonify(chart_data)


                                        #route pour les opérations globales

@app.route('/install', methods=['GET', 'POST'])
def install():
    if request.method == 'POST':
        file = request.files['yaml_file']
        resource_type = request.form.get('resource_type')
        if file and resource_type:
            file_path = os.path.join(temp_yaml_dir, file.filename)
            file.save(file_path)
            yaml_object_name = os.path.basename(file_path)
            if check_if_resource_exists(resource_type, yaml_object_name):
                message = f'L\'objet YAML "{yaml_object_name}" existe déjà dans le cluster.'
                return jsonify({'error': message})
            success, error_message = install_yaml(file_path)
            os.remove(file_path)
            if success:
                message = f'Fichier YAML "{yaml_object_name}" installé avec succès dans le cluster.'
                return jsonify({'success': message})
            else:
                message = f'Erreur lors de l\'installation du fichier YAML : {error_message}'
                return jsonify({'error': message})
            

    
@app.route('/yaml/<resource_type>/<namespace>/<resource_name>', methods=['GET'])
def get_resource_yaml(resource_type, namespace, resource_name):
    try:
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
        yaml_string = yaml.dump(resource, default_flow_style=False)
        return render_template('pods', yaml_string=yaml_string)
    except Exception as e:
        return str(e)


                                        #route pour les opérations sur les pods    

@app.route('/open_pod_shell/<pod_name>')
def open_pod_shell(pod_name):
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
    try:
        result = subprocess.check_output(f'kubectl exec -it {pod_name} -- {command}', shell=True, stderr=subprocess.STDOUT, text=True)
        return jsonify(result)
    except subprocess.CalledProcessError as e:
        return jsonify(e.output)

@app.route('/delete_pod', methods=['POST'])
def delete_pod():
    namespace = request.form.get('namespace')
    pod_name = request.form.get('name')
    core_api = client.CoreV1Api()
    try:
        delete_options = client.V1DeleteOptions()
        core_api.delete_namespaced_pod(pod_name, namespace, body=delete_options)
        return redirect(url_for('pods', success_message='Le pod a été supprimé avec succès.'))
    except client.rest.ApiException as e:
        error_message = f"Erreur lors de la suppression du pod : {e.reason}"
        return redirect(url_for('pods', error_message=error_message))

@app.route('/logs/<namespace>/<pod_name>', methods=['GET'])
def logs(namespace, pod_name):
    logs = get_pod_logs(namespace, pod_name)
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(logs=logs.splitlines())    
    return render_template('pods.html', logs=logs)     

@app.route('/pods', methods=['GET', 'POST'])
def pods():
    pod_name = request.args.get('namespace', 'default')
    yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]
    namespaces = get_available_namespaces()
    pods = get_pods_in_namespace(pod_name)
    return render_template('pods.html', pods=pods, yaml_files=yaml_files, namespaces=namespaces)

@app.route('/pod_details/<namespace>/<pod_name>', methods=['GET'])
def pod_details(namespace, pod_name):
    pod_details = get_pod_details(namespace, pod_name)
    formatted_pod_details = Markup(pod_details)
    return formatted_pod_details

                                    #route pour les opérations sur le déploiments

@app.route('/deployment', methods=['GET', 'POST'])
def deployment():
    deployment_name = request.args.get('namespace', 'default')
    yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]
    namespaces = get_available_namespaces()
    deployments = get_deployments_in_namespace(deployment_name)
    return render_template('deployment.html', deployments=deployments, yaml_files=yaml_files, namespaces=namespaces)

@app.route('/delete_deployment', methods=['POST'])
def delete_deployment():
    namespace = request.form.get('namespace')
    name = request.form.get('name')
    k8s_apps_v1 = client.AppsV1Api()
    try:
        delete_options = client.V1DeleteOptions()
        k8s_apps_v1.delete_namespaced_deployment(name, namespace, body=delete_options)
        return redirect(url_for('deployment', success_message='Le déploiement a été supprimé avec succès.'))
    except client.rest.ApiException as e:
        error_message = f"Erreur lors de la suppression du déploiement : {e.reason}"
        return redirect(url_for('deployment', error_message=error_message))


                                        #route pour les opérations sur le configmap

@app.route('/configmap', methods=['GET', 'POST'])
def configmap():
   ConfigMap_name = request.args.get('namespace', 'default')
   yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]
   namespaces = get_available_namespaces()     
   configmap_list = get_configmap_in_namespace(ConfigMap_name)
   return render_template('configmap.html', configmaps=configmap_list, yaml_files=yaml_files, namespaces=namespaces)


                                        #route pour les opérations sur le secret

@app.route('/secret', methods=['GET', 'POST'])
def secret():
    secret_name = request.args.get('namespace', 'default')
    yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]
    namespaces = get_available_namespaces()           
    secrets = get_secret_in_namespace(secret_name)
    return render_template('secret.html', secrets=secrets, yaml_files=yaml_files, namespaces=namespaces)


                                        #route pour les opérations sur le service

@app.route('/service', methods=['GET', 'POST'])
def service():
    service_name = request.args.get('namespace', 'default')
    yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]
    namespaces = get_available_namespaces() 
    service_list = get_service_in_namespace(service_name)
    return render_template('service.html', services=service_list, yaml_files=yaml_files, namespaces=namespaces)

                                        #route pour les opérations sur l'ingress

@app.route('/ingress', methods=['GET', 'POST'])
def ingress():
    ingress_name = request.args.get('namespace', 'default')
    yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]   
    namespaces = get_available_namespaces()
    ingress_list = get_ingresses_in_namespace(ingress_name)        
    return render_template('ingress.html', ingresses=ingress_list, yaml_files=yaml_files, namespaces=namespaces)

                                        #route pour les opérations sur le pvc

@app.route('/pvc', methods=['GET', 'POST'])
def pvc():
    pvc_name = request.args.get('namespace', 'default')
    yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]
    namespaces = get_available_namespaces()
    pvc_list = get_persistent_volume_claims_in_namespace(pvc_name)
    return render_template('pvc.html', pvc_list=pvc_list, yaml_files=yaml_files, namespaces=namespaces)


                                        #route pour les opérations sur le pv


@app.route('/pv', methods=['GET', 'POST'])
def pv():
    pv_name = request.args.get('namespace', 'default')
    yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]
    namespaces = get_available_namespaces()
    pv_list = get_persistent_volume_claims_in_namespace(pv_name)
    return render_template('pv.html', pv_list=pv_list, yaml_files=yaml_files, namespaces=namespaces)


                                        #route pour les opérations sur le statefullset

@app.route('/statefullset', methods=['GET', 'POST'])
def statefullset():
    statefullset_name = request.args.get('namespace', 'default')
    yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]
    namespaces = get_available_namespaces()
    statefullset_list = get_statefulsets_in_namespace(statefullset_name)
    return render_template('statefullset.html', statefullset_list=statefullset_list, yaml_files=yaml_files, namespaces=namespaces)


                                        #route pour les opérations sur le replicaset

@app.route('/replicatset', methods=['GET', 'POST'])
def replicatset():
    replicatset_name = request.args.get('namespace', 'default')
    yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]
    namespaces = get_available_namespaces()
    replicatset_list = get_replicasets_in_namespace(replicatset_name)
    return render_template('replicatset.html', replicatset_list=replicatset_list, yaml_files=yaml_files, namespaces=namespaces)


                                        #route pour les opérations sur le jobs

@app.route('/jobs', methods=['GET', 'POST'])
def jobs():
    jobs_name = request.args.get('namespace', 'default')
    yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]
    namespaces = get_available_namespaces()
    jobs_list = get_jobs_in_namespace(jobs_name)
    return render_template('jobs.html', jobs_listt=jobs_list, yaml_files=yaml_files, namespaces=namespaces)


                                        #route pour les opérations sur le cronjobs


@app.route('/cronjobs', methods=['GET', 'POST'])
def cronjobs():
    cronjobs_name = request.args.get('namespace', 'default')
    yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]
    namespaces = get_available_namespaces()
    cronjobs_list = get_cronjobs_in_namespace(cronjobs_name)
    return render_template('cronjobs.html', cronjobs_listt=cronjobs_list, yaml_files=yaml_files, namespaces=namespaces)


if __name__ == '__main__':
    socketio.run(app, debug=True)