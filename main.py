from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, Markup, session, Response
from flask_socketio import SocketIO
from kubernetes import client, config, utils
import os
import psutil
import mysql.connector
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
from trigger import *
from kubeconfig_generator import *
import openai


app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
socketio = SocketIO(app)

mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="",
    database="database"
)
mycursor = mydb.cursor()

openai.api_key = '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'

                                           #route index de l'application

@app.route('/', methods=['GET'])
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        txtname1 = request.form['txtname1']
        txtpass1 = request.form['txtpass1']
        mycursor.execute('SELECT roles FROM prs_info WHERE prs_name = %s AND prs_pass = %s', (txtname1, txtpass1,))
        roles = mycursor.fetchone()

        if roles:
            role = roles[0]
            session['username'] = txtname1
            return jsonify(success="Connexion réussie", role=role,)
        else:
            return jsonify(error="Veuillez vérifier votre nom d'utilisateur et mot de passe.")
    else:
        return render_template('login.html')

@app.route('/register', methods=['POST'])
def register():
    if request.method == 'POST':
        txtname = request.form['txtname']
        txtpass = request.form['txtpass']
        txtmail = request.form['txtmail']
        fonction = request.form['fonction']
        hash = request.form['txthash']

        mycursor.execute('SELECT * FROM cluster WHERE hash = %s', (hash,))
        cluster = mycursor.fetchone()

        if not cluster:
            return jsonify(error=f"Le hash spécifié n'existe pas dans la base de données.")
        elif not txtname or not txtpass or not txtmail or not fonction or not hash:
            return jsonify(error=f"Veuillez remplir tous les champs.")
        else:
            mycursor.execute('SELECT * FROM prs_info WHERE prs_name = %s', (txtname,))
            existing_user = mycursor.fetchone()

            if existing_user:
                return jsonify(error=f"Ce nom d'utilisateur est déjà enregistré.")
            else:
                mycursor.execute('INSERT INTO prs_info VALUES (NULL, %s, %s, %s, %s)', (txtname, txtpass, txtmail, fonction))
                mydb.commit()

                action = f"L'utilisateur {txtname} a été ajouté dans prs_info avec le hash {hash}"
                mycursor.execute('INSERT INTO tracking (action, prs_info_id, cluster_id) VALUES (%s, %s, %s)',(action, mycursor.lastrowid, cluster[0]))

                return jsonify(success=f"Compte enregistré avec succès!")

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))                        

@app.route('/home')
def home():
    if 'username' in session:
        username = session['username']
        mycursor.execute('SELECT * FROM prs_info WHERE prs_name = %s', (username,))
        user = mycursor.fetchone()

        logs = get_logs()
        cluster_details = get_cluster_details()
        Cluster = get_cluster()
        config.load_kube_config()
        contexts, _ = config.list_kube_config_contexts()
        clusters = [context['name'] for context in contexts]

        return render_template('admin.html', clusters=clusters, logs=logs, cluster_details=cluster_details, user=user, username=username, Cluster=Cluster)
    
    return redirect(url_for('login'))


@app.route('/devOps')
def devOps():
    if 'username' in session:
        username = session['username']
        
        mycursor.execute('SELECT * FROM prs_info WHERE prs_name = %s', (username,))
        user = mycursor.fetchone()

        mycursor.execute('''
            SELECT cluster.name_cluster
            FROM cluster
            JOIN tracking ON cluster.id = tracking.cluster_id
            JOIN prs_info ON tracking.prs_info_id = prs_info.id
            WHERE prs_info.prs_name = %s                          
        ''', (username,))
        cluster = mycursor.fetchall()               
        
        
        logs = get_logs()
        cluster_details = get_cluster_details()

        return render_template('devops.html', username=username, logs=logs, cluster_details=cluster_details, cluster=cluster, user=user)

    return redirect(url_for('login'))

@app.route('/testeur')
def testeur():
    if 'username' in session:
        username = session['username']
        mycursor.execute('SELECT * FROM prs_info WHERE prs_name = %s', (username,))
        user = mycursor.fetchone()

        mycursor.execute('''
            SELECT cluster.name_cluster
            FROM cluster
            JOIN tracking ON cluster.id = tracking.cluster_id
            JOIN prs_info ON tracking.prs_info_id = prs_info.id
            WHERE prs_info.prs_name = %s                          
        ''', (username,))
        cluster = mycursor.fetchall()          

        logs = get_logs()
        cluster_details = get_cluster_details()
        return render_template('testeur.html', username=username,  logs=logs, cluster_details=cluster_details, cluster=cluster, user=user)
            
    return redirect(url_for('login'))


@app.route('/connect', methods=['POST'])
def connect():
    selected_cluster = request.form.get('cluster')
    try:
        config.load_kube_config(context=selected_cluster)
        os.environ['KUBECONFIG'] = config.KUBE_CONFIG_DEFAULT_LOCATION
        return redirect(url_for('home'))
    except Exception as e:
        return f"Erreur de connexion au cluster : {str(e)}"

@app.route('/cluster_details')
def cluster_details():
    try:
        command = ["kubectl", "describe", "nodes", "minikube"]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        cluster_details = result.stdout
        return cluster_details
    except subprocess.CalledProcessError as e:
        error_message = f"Erreur : {e.stderr}"
        return jsonify({"error": error_message})
    

                        #route pour les opérations sur le user    

@app.route('/user', methods=['GET'])
def user():
    if 'username' in session:   
        username = session['username']
        mycursor.execute('SELECT * FROM prs_info WHERE prs_name = %s', (username,))
        user = mycursor.fetchone()

        mycursor.execute('SELECT * FROM prs_info')
        utilisateur = mycursor.fetchall()

        contexts, _ = config.list_kube_config_contexts()
        clusters = [context['name'] for context in contexts]

        return render_template('user.html', clusters=clusters, user=user, username=username, utilisateur=utilisateur)
    
    return redirect(url_for('login'))

@app.route('/historique', methods=['GET'])
def get_historique():
    username = request.args.get('username')
    mycursor.execute('''
            SELECT action
            FROM tracking
            JOIN prs_info ON tracking.prs_info_id = prs_info.id
            WHERE prs_info.prs_name = %s                          
        ''', (username,))
    
    historique = mycursor.fetchall()
    return jsonify(historique)


                                    #route pour les opérations sur le namespace  

@app.route('/namespace', methods=['GET'])
def namespace():
    if 'username' in session:   
        username = session['username']
        user = get_user_info(username)
        cluster = get_clusterall(username)
        namespace = get_namespace()
        return render_template('namespace.html', user=user, cluster=cluster, username=username, namespace=namespace)    
    return redirect(url_for('login'))

@app.route('/add_namespace', methods=['POST'])
def add_namespace():
    namespace_name = request.form['namespace_name']
    username = session['username']       
    try:
        v1 = client.CoreV1Api()
        body = client.V1Namespace(metadata=client.V1ObjectMeta(name=namespace_name))
        v1.create_namespace(body=body)

        cluster_name = get_clustername(username)

        action = f"L'utilisateur {username} a ajouté un namespace sous le nom {namespace_name} sur le cluster {cluster_name}"

        add_tracking(username, action)

        return jsonify(success=f"namespace créé avec succès!")
    except Exception as e:
        return jsonify(error=f"Erreur lors de la création du namespace")    

@app.route('/delete_namespace', methods=['GET'])
def delete_namespace():
    namespace_name = request.args.get('namespace_name')
    username = session['username']
    try:
        subprocess.run(["kubectl", "delete", "namespace", namespace_name])

        cluster_name = get_clustername(username)

        action = f"L'utilisateur {username} a supprimé un namespace sous le nom {namespace_name} sur le cluster {cluster_name}"

        add_tracking(username, action)

        return jsonify(success=True, message=f"Le namespace '{namespace_name}' a été supprimé avec succès.")
    except Exception as e:
        return jsonify(success=False, message=f"Erreur lors de la suppression du namespace : {e}")

@app.route('/namespace_details', methods=['GET'])
def get_namespace_details():
    namespace_name = request.args.get('namespace_name')
    try:
        process = subprocess.Popen(["kubectl", "describe", "namespace", namespace_name], stdout=subprocess.PIPE)
        output, _ = process.communicate()
        return output.decode('utf-8')
    except Exception as e:
        return f"Erreur lors de la récupération des détails du namespace : {e}"         


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
    username = session['username']
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

            cluster_name = get_clustername(username)

            action = f"L'utilisateur {username} a installé un {resource_type} sous le nom {yaml_object_name} sur le cluster {cluster_name}"

            add_tracking(username, action)

            os.remove(file_path)
            if success:         
                message = f'Fichier YAML "{yaml_object_name}" installé avec succès dans le cluster.'
                return jsonify({'success': message})
            else:
                message = f'Erreur lors de l\'installation du fichier YAML : {error_message}'
                return jsonify({'error': message})
            

@app.route('/install_component', methods=['POST'])
def install_component():
    component_yaml = request.form['component_yaml']
    try:
        with open('component.yaml', 'w') as f:
            f.write(component_yaml)

        subprocess.run(['kubectl', 'apply', '-f', 'component.yaml'])

        save_folder = 'fichier_installer'
        if not os.path.exists(save_folder):
            os.makedirs(save_folder)

        os.rename('component.yaml', os.path.join(save_folder, 'component.yaml'))

        message = f'Composant installé et fichier YAML sauvegardé avec succès!'
        return jsonify({'success': message})
    except Exception as e:
        message = f"Erreur lors de l'installation du composant : {str(e)}"
        return jsonify({'success': message})


                                        #route pour les opérations sur les pods    

@app.route('/open_pod_shell/<pod_name>')
def open_pod_shell(pod_name):
    command = f'kubectl exec -ti {pod_name} /bin/bash'
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
    username = session['username']
    try:
        delete_options = client.V1DeleteOptions()
        core_api.delete_namespaced_pod(pod_name, namespace, body=delete_options)

        cluster_name = get_clustername(username)

        action = f"L'utilisateur {username} a supprimer un pod sous le nom {pod_name} sur le cluster {cluster_name}"

        add_tracking(username, action)

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
    if 'username' in session:
        username = session['username']
        user = get_user_info(username)
        cluster = get_clusterall(username)
        selected_namespace = request.args.get('namespace', 'default')  # Récupère le namespace sélectionné depuis les paramètres d'URL
        yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]
        namespaces = get_available_namespaces()
        pods = get_pods_in_namespace(selected_namespace)  # Utilisez le namespace sélectionné ici pour récupérer les pods
        return render_template('pods.html', pods=pods, user=user, username=username, cluster=cluster, yaml_files=yaml_files, namespaces=namespaces, selected_namespace=selected_namespace)
    
    return redirect(url_for('login'))



@app.route('/pod_details/<namespace>/<pod_name>', methods=['GET'])
def pod_details(namespace, pod_name):
    pod_details = get_pod_details(namespace, pod_name)
    formatted_pod_details = Markup(pod_details)
    return formatted_pod_details

@app.route('/pod_yaml/<namespace>/<pod_name>', methods=['GET'])
def get_pod_yaml(namespace, pod_name):
    pod_yaml = get_pod_yaml(namespace, pod_name)
    formated_pod_yaml = Markup(pod_yaml)
    return formated_pod_yaml

@app.route('/update_pod', methods=['POST'])
def update_pod():
    try:
        namespace = request.form.get('namespace')
        pod_name = request.form.get('pod_name')
        new_image = request.form.get('new_image')
        configuration = client.Configuration()
        configuration.namespace = namespace
        api_instance = client.CoreV1Api(client.ApiClient(configuration))
        pod = api_instance.read_namespaced_pod(name=pod_name, namespace=namespace)
        pod.spec.containers[0].image = new_image
        api_instance.patch_namespaced_pod(name=pod_name, namespace=namespace, body=pod)

        return jsonify(success=True, message="Pod mis à jour avec succès.")
    except Exception as e:
        return jsonify(success=False, error=str(e))

                                    #route pour les opérations sur le déploiments

@app.route('/deployment', methods=['GET', 'POST'])
def deployment():
    if 'username' in session:
        username = session['username']
        user = get_user_info(username)
        cluster = get_clusterall(username)
        selected_namespace = request.args.get('namespace', 'default')
        yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]
        namespaces = get_available_namespaces()
        deployments = get_deployments_in_namespace(selected_namespace)
        return render_template('deployment.html', deployments=deployments, user=user, cluster=cluster, username=username, yaml_files=yaml_files, namespaces=namespaces, selected_namespace=selected_namespace)
    
    return redirect(url_for('login'))   
@app.route('/delete_deployment', methods=['POST'])
def delete_deployment():
    namespace = request.form.get('namespace')
    name = request.form.get('name')
    k8s_apps_v1 = client.AppsV1Api()
    username = session['username']
    try:
        delete_options = client.V1DeleteOptions()
        k8s_apps_v1.delete_namespaced_deployment(name, namespace, body=delete_options)

        cluster_name = get_clustername(username)

        action = f"L'utilisateur {username} a supprimé un déploiment sous le nom {name} sur le cluster {cluster_name}"

        add_tracking(username, action)

        return redirect(url_for('deployment', success_message='Le déploiement a été supprimé avec succès.'))
    except client.rest.ApiException as e:
        error_message = f"Erreur lors de la suppression du déploiement : {e.reason}"
        return redirect(url_for('deployment', error_message=error_message))

@app.route('/deploy_details/<namespace>/<deployment_name>', methods=['GET'])
def deploy_details(namespace, deployment_name):
    deploy_details = get_deploy_details(namespace, deployment_name)
    formatted_deploy_details = Markup(deploy_details)
    return formatted_deploy_details

@app.route('/update_deployment', methods=['PATCH'])
def update_deployment():
    data = request.get_json()
    namespace = data.get('namespace')
    deployment_name = data.get('deploymentName')
    replicas = int(data.get('replicas'))
    username = session['username']
    try:
        v1 = client.AppsV1Api()
        deployment = v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)
        deployment.spec.replicas = replicas
        v1.patch_namespaced_deployment(name=deployment_name, namespace=namespace, body=deployment)
        cluster_name = get_clustername(username)

        action = f"L'utilisateur {username} a mis à jour un déploiment sous le nom {deployment_name} sur le cluster {cluster_name}"

        add_tracking(username, action)

        return jsonify({'message': 'Déploiement mis à jour avec succès'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500 


                                        #route pour les opérations sur le configmap

@app.route('/configmap', methods=['GET', 'POST'])
def configmap():
    if 'username' in session:
        username = session['username']
        user = get_user_info(username)
        cluster = get_clusterall(username)
        selected_namespace = request.args.get('namespace', 'default')
        yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]
        namespaces = get_available_namespaces()     
        configmap_list = get_configmap_in_namespace(selected_namespace)
        return render_template('configmap.html', user=user, cluster=cluster, username=username, configmaps=configmap_list, yaml_files=yaml_files, namespaces=namespaces, selected_namespace=selected_namespace)

    return redirect(url_for('login')) 

@app.route('/configmap_details/<namespace>/<configMap_name>', methods=['GET'])
def config_details(namespace, configMap_name):
    config_details = get_config_details(namespace, configMap_name)
    formatted_config_details = Markup(config_details)
    return formatted_config_details

                                        #route pour les opérations sur le secret

@app.route('/secret', methods=['GET', 'POST'])
def secret():
    if 'username' in session:
        username = session['username']
        user = get_user_info(username)
        cluster = get_clusterall(username)
        selected_namespace = request.args.get('namespace', 'default')
        yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]
        namespaces = get_available_namespaces()           
        secrets = get_secret_in_namespace(selected_namespace)
        return render_template('secret.html', secrets=secrets, user=user, username=username, cluster=cluster, yaml_files=yaml_files, namespaces=namespaces, selected_namespace=selected_namespace)
    return redirect(url_for('login')) 

@app.route('/secret_details/<namespace>/<secret_name>', methods=['GET'])
def secret_details(namespace, secret_name):
    secret_details = get_secret_details(namespace, secret_name)
    formatted_secret_details = Markup(secret_details)
    return formatted_secret_details

                                        #route pour les opérations sur le service

@app.route('/service', methods=['GET', 'POST'])
def service():
    if 'username' in session:
        username = session['username']
        user = get_user_info(username)
        cluster = get_clusterall(username)
        selected_namespace = request.args.get('namespace', 'default')
        yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]
        namespaces = get_available_namespaces() 
        service_list = get_service_in_namespace(selected_namespace)
        return render_template('service.html', services=service_list, username=username, cluster=cluster, user=user, yaml_files=yaml_files, namespaces=namespaces, selected_namespace=selected_namespace)
    return redirect(url_for('login')) 

@app.route('/service_details/<namespace>/<service_name>', methods=['GET'])
def service_details(namespace, service_name):
    service_details = get_service_details(namespace, service_name)
    formatted_service_details = Markup(service_details)
    return formatted_service_details
    

@app.route('/delete_service', methods=['POST'])
def delete_service():
    namespace = request.form.get('namespace')
    service_name = request.form.get('name')
    username = session['username']
    try:
        cmd = f'kubectl delete service {service_name} -n {namespace}'
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)

        cluster_name = get_clustername(username)

        action = f"L'utilisateur {username} a supprimé un service sous le nom {service_name} sur le cluster {cluster_name}"

        add_tracking(username, action)

        return "Service supprimé avec succès!"
    except Exception as e:
        return f"Erreur lors de la suppression du service : {str(e)}"
                                        
                                        #route pour les opérations sur l'ingress

@app.route('/ingress', methods=['GET', 'POST'])
def ingress():
    if 'username' in session:
        username = session['username']
        user = get_user_info(username)
        cluster = get_clusterall(username)
        selected_namespace = request.args.get('namespace', 'default')
        yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]   
        namespaces = get_available_namespaces()
        ingress_list = get_ingresses_in_namespace(selected_namespace)        
        return render_template('ingress.html', ingresses=ingress_list, username=username, user=user, cluster=cluster, yaml_files=yaml_files, namespaces=namespaces, selected_namespace=selected_namespace)
    return redirect(url_for('login')) 

@app.route('/ingress_details/<namespace>/<ingress_name>', methods=['GET'])
def ingress_details(namespace, ingress_name):
    ingress_details = get_ingress_details(namespace, ingress_name)
    formatted_ingress_details = Markup(ingress_details)
    return formatted_ingress_details

                                        #route pour les opérations sur le pvc

@app.route('/pvc', methods=['GET', 'POST'])
def pvc():
    if 'username' in session:
        username = session['username']
        user = get_user_info(username)
        cluster = get_clusterall(username)
        selected_namespace = request.args.get('namespace', 'default')
        yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]
        namespaces = get_available_namespaces()
        pvc_list = get_persistent_volume_claims_in_namespace(selected_namespace)
        return render_template('pvc.html', pvc_list=pvc_list, username=username, user=user, cluster=cluster, yaml_files=yaml_files, namespaces=namespaces, selected_namespace=selected_namespace)
    return redirect(url_for('login')) 

@app.route('/pvc_details/<namespace>/<pvc_name>', methods=['GET'])
def pvc_details(namespace, pvc_name):
    pvc_details = get_pvc_details(namespace, pvc_name)
    formatted_pvc_details = Markup(pvc_details)
    return formatted_pvc_details


                                        #route pour les opérations sur le pv


@app.route('/pv', methods=['GET', 'POST'])
def pv():
    if 'username' in session:
        username = session['username']
        user = get_user_info(username)
        cluster = get_clusterall(username)
        selected_namespace = request.args.get('namespace', 'default')
        yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]
        namespaces = get_available_namespaces()
        pv_list = get_persistent_volume_in_namespace(selected_namespace)
        return render_template('pv.html', pv_list=pv_list, username=username, user=user, cluster=cluster, yaml_files=yaml_files, namespaces=namespaces, selected_namespace=selected_namespace)
    return redirect(url_for('login')) 

@app.route('/pv_details/<namespace>/<pv_name>', methods=['GET'])
def pv_details(namespace, pv_name):
    pv_details = get_pv_details(namespace, pv_name)
    formatted_pv_details = Markup(pv_details)
    return formatted_pv_details

                                        #route pour les opérations sur le statefullset

@app.route('/statefullset', methods=['GET', 'POST'])
def statefullset():
    if 'username' in session:
        username = session['username']
        user = get_user_info(username)
        cluster = get_clusterall(username)
        selected_namespace = request.args.get('namespace', 'default')
        yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]
        namespaces = get_available_namespaces()
        statefullset_list = get_statefulsets_in_namespace(selected_namespace)
        return render_template('statefullset.html', statefullset_list=statefullset_list, user=user, username=username, cluster=cluster, yaml_files=yaml_files, namespaces=namespaces, selected_namespace=selected_namespace)
    return redirect(url_for('login')) 

@app.route('/statefullset_details/<namespace>/<statefullset_name>', methods=['GET'])
def statefullset_details(namespace, statefullset_name):
    statefullset_details = get_statefullset_details(namespace, statefullset_name)
    formatted_statefullset_details = Markup(statefullset_details)
    return formatted_statefullset_details

                                        #route pour les opérations sur le replicaset

@app.route('/replicatset', methods=['GET', 'POST'])
def replicatset():
    if 'username' in session:
        username = session['username']
        user = get_user_info(username)
        cluster = get_clusterall(username)
        selected_namespace = request.args.get('namespace', 'default')
        yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]
        namespaces = get_available_namespaces()
        replicatset_list = get_replicasets_in_namespace(selected_namespace)
        return render_template('replicatset.html', replicatset_list=replicatset_list, username=username, user=user, cluster=cluster, yaml_files=yaml_files, namespaces=namespaces, selected_namespace=selected_namespace)
    return redirect(url_for('login')) 

@app.route('/replicatset_details/<namespace>/<statefullset_name>', methods=['GET'])
def replicatset_details(namespace, replicatset_name):
    replicatset_details = get_replicatset_details(namespace, replicatset_name)
    formatted_replicatset_details = Markup(replicatset_details)
    return formatted_replicatset_details

                                        #route pour les opérations sur le jobs

@app.route('/jobs', methods=['GET', 'POST'])
def jobs():
    if 'username' in session:
        username = session['username']
        user = get_user_info(username)
        cluster = get_clusterall(username)
        selected_namespace = request.args.get('namespace', 'default')
        yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]
        namespaces = get_available_namespaces()
        jobs_list = get_jobs_in_namespace(selected_namespace)
        return render_template('jobs.html', jobs_listt=jobs_list, user=user, username=username, cluster=cluster, yaml_files=yaml_files, namespaces=namespaces, selected_namespace=selected_namespace)
    return redirect(url_for('login')) 

                                        #route pour les opérations sur le cronjobs


@app.route('/cronjobs', methods=['GET', 'POST'])
def cronjobs():
    if 'username' in session:
        username = session['username']
        user = get_user_info(username)
        cluster = get_clusterall(username)
        selected_namespace = request.args.get('namespace', 'default')
        yaml_files = [f for f in os.listdir(yaml_dir) if f.endswith(('.yaml', '.yml'))]
        namespaces = get_available_namespaces()
        cronjobs_list = get_cronjobs_in_namespace(selected_namespace)
        return render_template('cronjobs.html', cronjobs_listt=cronjobs_list, user=user, username=username, cluster=cluster, yaml_files=yaml_files, namespaces=namespaces, selected_namespace=selected_namespace)
    return redirect(url_for('login'))

@app.route('/generate_kubeconfig', methods=['POST'])
def generate_kubeconfig_route():
    username = request.form['username']
    client_cert_path = request.form['client_cert']
    client_key_path = request.form['client_key']

    kubeconfig_content = generate_kubeconfig(username, client_cert_path, client_key_path)

    response = Response(kubeconfig_content, content_type='application/x-yaml')
    response.headers['Content-Disposition'] = f'attachment; filename={username}_kubeconfig.yaml'
    return response


@app.route('/ia')
def ia():
    return render_template('ia.html')


@app.route('/get_openai_response', methods=['POST'])
def get_openai_response():
    user_message = request.json['message']

    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=f"L'utilisateur dit : {user_message}\nAssistance virtuelle :",
            max_tokens=400  
        )

        openai_response = response.choices[0].text.strip()
        return jsonify({'message': openai_response})
    except Exception as e:
        print(f"Erreur OpenAI : {str(e)}")
        return jsonify({'message': "Erreur lors de la génération de la réponse."})

if __name__ == '__main__':
    socketio.run(app, host='relia-kubernetes.controls', debug=True)