from flask import flash
from kubernetes import client, config, utils
import os
import subprocess

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

def apply_yaml(file_path):
    try:
        cmd = f'kubectl apply -f {file_path}'
        os.system(cmd)
        flash(f'Fichier YAML "{file_path.filename}" installé avec succès dans le cluster.', 'success')
    except subprocess.CalledProcessError as e:
        flash(f'Erreur lors de l\'installation du fichier YAML : {str(e)}', 'error') 

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

start_minikube_proxy()    