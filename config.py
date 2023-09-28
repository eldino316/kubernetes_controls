import os

os.environ['KUBECONFIG'] = os.path.expandvars('%USERPROFILE%\\.kube\\config')
yaml_dir = os.path.expandvars('D:\\PROJET MEMOIRE\\maquette\\kubernetes\\temp_yaml')
temp_yaml_dir = 'temp_yaml'
os.makedirs(temp_yaml_dir, exist_ok=True)