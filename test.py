from flask import Flask, render_template, request
import subprocess
import os

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('test.html')

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

        return "Composant installé et fichier YAML sauvegardé avec succès!"
    except Exception as e:
        return f"Erreur lors de l'installation du composant : {str(e)}"

if __name__ == '__main__':
    app.run(debug=True)
