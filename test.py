from kubernetes import client
from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def index():
    v1 = client.CoreV1Api()
    namespaces = v1.list_namespace().items
    name = [namespace.metadata.name for namespace in namespaces]

    return render_template('test.html', namespaces=name)


if __name__ == '__main__':
    app.run(debug=True)
