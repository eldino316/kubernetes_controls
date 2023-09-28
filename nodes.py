import datetime
from kubernetes import client, config, utils
import os
import requests
import pytz

kubernetes_api_url = "http://localhost:8001"


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