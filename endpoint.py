from kubernetes import client


def get_endpoints(namespace):
    v1 = client.CoreV1Api()
    endpoints = v1.list_namespaced_endpoints(namespace, watch=False)

    endpoints_data = []
    for endpoint in endpoints.items:
            for subset in endpoint.subsets:
                for address in subset.addresses:
                    endpoints_data.append({
                        "namespace": endpoint.metadata.namespace,
                        "service_name": endpoint.metadata.name,
                        "ip": address.ip,
                        "ports": [port.port for port in subset.ports]
                    })
    
    return  endpoints_data