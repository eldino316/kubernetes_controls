from flask import Flask, render_template, request, redirect, url_for, jsonify, flash, Markup
import subprocess
from kubernetes import client, config, utils
import os
import requests

app = Flask(__name__)

def get_pod_details(namespace, pod_name):
    try:
        # Exécutez la commande kubectl describe pods
        command = ["kubectl", "describe", "pods", pod_name, "-n", namespace]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
        
        # Récupérez la sortie de la commande
        pod_details = result.stdout
        
        # Renvoyez les détails au format JSON
        return pod_details
    except subprocess.CalledProcessError as e:
        # La commande a échoué, vous pouvez gérer l'erreur ici
        return {"error": f"Erreur : {e.stderr}"}
    
def get_pod_logs(namespace, pod_name):
    try:
        # Utilisez l'API Kubernetes Python pour récupérer les logs du pod
        api_instance = client.CoreV1Api()
        logs = api_instance.read_namespaced_pod_log(
            name=pod_name, namespace=namespace)
        return logs
    except Exception as e:
        return str(e)
    
def get_pods_in_namespace(namespace):
    core_api = client.CoreV1Api()
    pods = core_api.list_namespaced_pod(namespace).items
    return pods 