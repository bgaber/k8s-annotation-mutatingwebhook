# get cluster_type, environment_type and region from the cluster-info ConfigMap in the Deploy namespace

import json
from flask import Flask, request, jsonify
import base64
import logging
from kubernetes import client, config
from kubernetes.client.rest import ApiException

app = Flask(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Log level: can be DEBUG, INFO, WARNING, ERROR, CRITICAL
    format='%(asctime)s - %(levelname)s - %(message)s',  # Log format
    handlers=[
        logging.StreamHandler()  # Output logs to stdout/stderr
    ]
)
logger = logging.getLogger(__name__)  # Create a logger

# Initialize Kubernetes client
config.load_incluster_config()
core_v1_api = client.CoreV1Api()

def get_value_from_configmap(key, description):
    """Fetch a specific value from the 'cluster-info' ConfigMap in the 'deploy' namespace."""
    try:
        # Read ConfigMap
        cluster_info = core_v1_api.read_namespaced_config_map(name="cluster-info", namespace="deploy")

        if cluster_info and cluster_info.data:
            value = cluster_info.data.get(key, f"N/A. No {description} found")
            logger.info(f"{description.capitalize()}: {value}")
            return value
        else:
            logger.warning(f"ConfigMap 'cluster-info' is empty or missing 'data' field.")
            return f"N/A. No {description} found"
    
    except client.exceptions.ApiException as e:
        if e.status == 404:
            logger.warning(f"ConfigMap 'cluster-info' not found. Returning default for {description}.")
            return f"N/A. No {description} found"
        else:
            logger.error(f"Error fetching ConfigMap: {str(e)}")
            raise  # Re-raise unexpected errors

    except config.ConfigException as e:
        logger.error(f"Error loading kube config: {str(e)}")
        return f"N/A. No {description} found"

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return f"N/A. No {description} found"

@app.route('/mutate', methods=['POST'])
def mutate():
    """Handles admission requests to mutate Pods."""
    try:
        # Much of the following code was taken from update.py written by Alexandru Grecu

        # Read the admission review request JSON body
        admission_review = request.get_json()

        # Ensure the request is valid
        if admission_review:
            logger.debug(f"AdmissionReview Request: {json.dumps(admission_review)}")
        else:
            logger.warning("Received an invalid request with no JSON payload.")
            return jsonify({"error": "Invalid request"}), 400

        # Extract pod metadata (name, namespace, and labels) from the request body
        pod_metadata = admission_review["request"]["object"]["metadata"]

        pod_name     = pod_metadata.get("name", "unnamed")       # Default to "unnamed" if name is not set
        namespace    = pod_metadata.get("namespace", "default")  # Default to "default" if namespace is not set
        labels       = pod_metadata.get("labels", {})            # Default to empty dict if labels are missing
        annotations  = pod_metadata.get("annotations", {})       # Default to empty dict if annotations are missing

        # Extract labels safely
        client_name  = labels.get('client', 'client-label-not-found') if labels else 'labels-not-found'
        environment  = labels.get('environment', 'environment-label-not-found') if labels else 'labels-not-found'
        release      = labels.get('release', 'release-label-not-found') if labels else 'labels-not-found'

        # Extract Helm release name from annotations
        release      = annotations.get('meta.helm.sh/release-name', release) if annotations else 'N/A. No annotations found'

        logger.info(f"Received mutation request for Pod: {pod_name} in Namespace: {namespace}")

        # Fetch the values from cluster-info configmap
        cluster_type = get_value_from_configmap('cluster_type', 'color')
        environment_type = get_value_from_configmap('environment_type', 'environment type')
        region = get_value_from_configmap('region', 'region')

        # Open and read the file into a List
        file_path = "/data/live-list.txt"
        try:
            with open(file_path, "r") as file:
                # Read each line, strip any surrounding whitespace (like newlines), and add to a list
                live_namespaces = [line.strip() for line in file]
            logger.info(f"Loaded live namespaces from {file_path}")
        except FileNotFoundError:
            logger.warning("The file {file_path} was not found")
        except PermissionError:
            logger.error("You do not have permission to open {file_path}")

        # Set the 'live' label based on the namespace
        live_value = "true" if namespace in live_namespaces else "false"

        # Set the 'kind' label based on the labels object
        if 'statefulset.kubernetes.io/pod-name' in labels:
            kind = "Stateful"
        else:
            kind = "Stateless"

        ids = {}
        # Open and read the file into a Nested Dictionary
        file_path = "/data/id-nested-dict.txt"
        try:
            with open(file_path, 'r') as file:
                for line in file:
                    if ':' in line:
                        key, value = line.strip().split(':', 1)
                        ids[key] = json.loads(value)
            logger.info(f"Loaded IDs from {file_path}")
        except FileNotFoundError:
            logger.warning("The file {file_path} was not found")
        except PermissionError:
            logger.error("You do not have permission to open {file_path}")

        matching_id = get_matching_id(pod_name, ids)
        
        if matching_id:
            service = matching_id.get('service', 'service-label-not-found')
            role    = matching_id.get('role', 'role-label-not-found')
        else:
            service = 'service-label-not-found'
            role    = 'role-label-not-found'

        service = labels.get('service', service) # preserve the value of the service variable if the 'service' key is not found in the 'labels' dictionary
        role    = labels.get('role', role)       # preserve the value of the role variable if the 'role' key is not found in the 'labels' dictionary

        # Define the annotation to be added
        annotation_tags = {
            "env": f"{environment_type}",
            "cluster_type": f"{cluster_type}",
            "namespace": f"{namespace}",
            "client_name": f"{client_name}",
            "client_environment": f"{environment}",
            "release": f"{release}",
            "live": f"{live_value}",
            "service": f"{service}",
            "role": f"{role}",
            "kind": f"{kind}",
            "region": f"{region}",
        }

        # Ensure the annotations field exists before adding to it
        patch = []

        # Check if annotations exist, if not, create the annotations field
        if "annotations" not in pod_metadata:
            patch.append({"op": "add", "path": "/metadata/annotations", "value": {}})

        # Add the actual annotation key-value
        patch.append({
            "op": "add",
            "path": "/metadata/annotations/ad.datadoghq.com~1tags",  # "~1" escapes "/"
            "value": json.dumps(annotation_tags)  # Convert dictionary to JSON string
        })

        # Encode the patch to base64
        patch_base64 = base64.b64encode(json.dumps(patch).encode()).decode()

        # Prepare the admission review response
        admission_response = {
            "uid": admission_review['request']['uid'],
            "allowed": True,
            "patchType": "JSONPatch",
            "patch": patch_base64
        }

        # Return the admission review response
        response = {
            "apiVersion": "admission.k8s.io/v1",
            "kind": "AdmissionReview",
            "response": admission_response
        }

        logger.info(f"Label mutation applied to the {pod_name} Pod in the {namespace} Namespace.")
        return jsonify(response)

    except Exception as e:
        # Log the error and return a 500 status code
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({"error": "An internal error occurred"}), 500

def get_matching_id(metadata_name, ids_dict):
    # Iterate through the keys in the dictionary
    for key in ids_dict:
        # Check if the key is contained in the metadata.name string
        if key in metadata_name:
            return ids_dict[key]
    return None

if __name__ == '__main__':
    try:
        logger.info("Starting the webhook server...")
        app.run(host='0.0.0.0', port=443, ssl_context=('/tls/tls.crt', '/tls/tls.key'))
    except Exception as e:
        logger.critical(f"Error starting the webhook server: {str(e)}")
