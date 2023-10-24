def generate_kubeconfig(username, client_cert_path, client_key_path):
    kubeconfig_content = f'''
apiVersion: v1
kind: Config
users:
- name: {username}
  user:
    client-certificate: {client_cert_path}
    client-key: {client_key_path}
clusters:
- name: my-cluster
  cluster:
    server: https://kubernetes-api-server:6443
contexts:
- name: my-context
  context:
    user: {username}
    cluster: my-cluster
current-context: my-context
'''
    return kubeconfig_content
