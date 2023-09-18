from flask import Flask, render_template, request, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import FileField
from kubernetes import client, config
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'

# Configurez le client Kubernetes
config.load_kube_config()

# Fonction pour appliquer un fichier YAML
def apply_yaml(file_path):
    cmd = f'kubectl apply -f {file_path}'
    os.system(cmd)

# Créez un formulaire Flask-WTF pour le téléchargement de fichiers
class UploadForm(FlaskForm):
    file = FileField('Sélectionnez un fichier YAML')

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    form = UploadForm()
    if form.validate_on_submit():
        file = form.file.data
        if file:
            # Créez le répertoire temporaire s'il n'existe pas
            temp_dir = 'temp'
            os.makedirs(temp_dir, exist_ok=True)

            # Générez un chemin de fichier unique en utilisant le nom du fichier original
            file_path = os.path.join(temp_dir, file.filename)

            # Sauvegardez le fichier YAML temporairement sur le serveur
            file.save(file_path)

            # Appliquez le fichier YAML
            apply_yaml(file_path)

            # Supprimez le fichier temporaire
            os.remove(file_path)

            return redirect(url_for('upload_file'))
    return render_template('upload.html', form=form)


if __name__ == '__main__':
    app.run(debug=True)
