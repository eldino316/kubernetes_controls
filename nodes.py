from flask import Flask, render_template, jsonify
from kubernetes import client, config

app = Flask(__name__)

# Chargez la configuration Kubernetes (par exemple, depuis le fichier kubeconfig)
config.load_kube_config()

@app.route('/')
def index():
    return render_template('node.html')

@app.route('/get_node_info')
def get_node_info():
    try:
        v1 = client.CoreV1Api()
        nodes = v1.list_node()
        
        # Sélectionnez un nœud (vous pouvez personnaliser cette logique)
        selected_node = nodes.items[0]

        # Obtenez des informations sur le nœud
        node_name = selected_node.metadata.name
        cpu_capacity = selected_node.status.capacity['cpu']
        ram_capacity = selected_node.status.capacity['memory']

        # Retournez les informations au format JSON
        node_info = {
            'node_name': node_name,
            'cpu_capacity': cpu_capacity,
            'ram_capacity': ram_capacity
        }

        return jsonify(node_info)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
