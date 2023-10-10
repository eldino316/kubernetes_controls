from flask import Flask, render_template, request, jsonify
from kubernetes import client, config

app = Flask(__name__)

@app.route('/')
def get_deployment_info():
    try:
        # Chargez la configuration Kubernetes à partir du fichier kubeconfig
        config.load_kube_config()

        # Créez un client API Kubernetes
        api_instance = client.AppsV1Api()

        # Spécifiez le namespace et le nom du déploiement que vous souhaitez récupérer
        namespace = 'default'
        deployment_name = 'nginx-deployment'

        # Récupérez les informations sur le déploiement
        deployment_info = api_instance.read_namespaced_deployment(name=deployment_name, namespace=namespace)

        # Renvoyez les informations sous forme de réponse HTML à l'aide du template
        return render_template('test.html', deployment_info=deployment_info)

    except Exception as e:
        # Gérez les erreurs ici
        return str(e), 500
    
@app.route('/update_deployment', methods=['PATCH'])
def update_deployment():
    data = request.get_json()
    namespace = data.get('namespace')
    deployment_name = data.get('deploymentName')
    replicas = int(data.get('replicas'))

    try:
        v1 = client.AppsV1Api()

        # Obtenez le déploiement existant
        deployment = v1.read_namespaced_deployment(name=deployment_name, namespace=namespace)

        # Mettez à jour le nombre de réplicas dans le déploiement
        deployment.spec.replicas = replicas

        # Effectuez la mise à jour du déploiement
        v1.patch_namespaced_deployment(name=deployment_name, namespace=namespace, body=deployment)

        return jsonify({'message': 'Déploiement mis à jour avec succès'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500    

if __name__ == '__main__':
    app.run(debug=True)
