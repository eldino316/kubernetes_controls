from flask import Flask, render_template, jsonify
import psutil

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('test.html')

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


if __name__ == '__main__':
    app.run(debug=True)
