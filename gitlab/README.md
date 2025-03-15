# Overview

This document explains how to setup the GitLab Pipeline automation of the Helm Chart package that installs the K8s Annotation MutatingWebhook solution using Helm templates and values file.

# Architecture and Workflow 

**Color Code Legend for workflow diagram**
- <span style="color: blue;">Blue</span>: Files that can trigger the pipeline
- <span style="color: yellow;">Yellow</span>: External projects 
- <span style="color: green;">Green</span>: Pipeline stages

![alt text](images/workflow-diagram.png)

## Steps to Run the Pipeline

1. **Clone the Repository**: Start by cloning this repository to your local machine.

2. **Create a Feature Branch**: Create a new branch from the main branch to implement your changes.

3. **Update Configuration Files**: Modify one or more of the following files as needed:

    a. `configmap.yaml` in the helm/k8s-annotation-mutatingwebhook/templates folder

    b. `mutatingwebhookconfiguration.yaml` in the regions folder

    c. `gitlab-ci.yml`

    d. `common-steps-template.yml`

4. **Commit Your Changes**: After making the necessary updates, commit your changes and push them to your feature branch.

5. **Clone repo to Linux CLI**: Required to setup K8s Service Account.

6. **Service Account Setup**: Described below under Linux CLI Prerequisites.

7. **Trigger the Pipeline**: Pushing your changes will automatically trigger the pipeline.

8. **Automatic Job Execution**: The linting, testing, and security scanning jobs will run automatically. Note that the security scan executes as a separate job.

9. **Manual Deployment**: The deployment job will need to be triggered manually once the previous jobs are completed.

![alt text](images/pipeline.png)


# Folder Structure
The repository follows a specific folder structure to organize environment specific configurations:

```

├── regions/
│   ├── {region-name}/
│   │   ├── {env-name}/
│   │   │   ├── green/
│   │   │   └── blue/     
├── service-account/
│   ├── serviceaccount.yaml
├── .gitlab-ci.yml
├── common-steps-template.yml

``` 

References from external repositories

```
For Aquasec integration
- project: "devops/tecsys-gitlab-ci"

For Pipeline Base image
- project: "ops/noc/noc-base-docker-images"

```

1. `regions/{region-name}/cluster-color/`: contains environment-specific configurations for different regions and clusters. 
For instance, regions/us-east-1/dev/green/ and regions/us-east-1/dev/blue/ represent two clusters (green and blue) within the dev environment for the us-east-1 region.

2. `service-account/serviceaccount.yaml`: Contains the Kubernetes service account configuration used in the pipeline for accessing the clusters.

3. `common-steps-template.yml`: is a template file for keeping the code dry and is referenced in `.gitlab-ci.yml`.

4. `.gitlab-ci.yml` : is the yaml file for configuring the pipeline.

5. The pipeline integrates with Aquasec for security and vulnerability scanning of docker images, configuration files and code. This is done by referencing the `- project: "devops/tecsys-gitlab-ci"` setup by the R&D Security team. For any issues with the aquasec scan, please reach out to Sally Szeto. 

6. The base image used in the pipeline has all the required packages built into it and is stored in Artifactory. When the docker file is updated, the new image gets pushed to Artifactory repository and is referenced in this repository's pipeline. This is controlled by this project `- project: "ops/noc/noc-base-docker-images/datadog-k8s-pipeline"`.

# GitLab CI Pipeline Stages
The CI pipeline (.gitlab-ci.yml) is designed to support various stages for a complete CI/CD lifecycle. 

1. **Stages**

    `lint`: Linting jobs for validating configuration and code quality in different environments.

    `security-scan`: Uses AquaSec Trivy for repository and container security scanning. For more information on Aquasec Trivy,  refer [Trivy](https://github.com/aquasecurity/trivy).

    `test`: Executes test jobs on the dev kubernetes cluster before deployment. It runs a helm diff which will illustrate what components are changing with the new update, it also deploys the changes to the dev kubernetes cluster for testing and validations.

    `deploy-mutatingwebhook`: Deploys updates to the mutatingwh namespace using Helm to different kubernetes environments.

2. **Job Definitions**

    **Lint Jobs**: Linting jobs are specific to environments and are executed to check code quality in different clusters.

    ```
    lint-dev-green:
    extends: .lint-job-template
    variables:
        ENV_PATH: "regions/us-east-1/dev/green"
    ```
    **Security Scan Jobs**: AquaSec is integrated to perform security scans on the repository, including a full scan and manifest upload.

    ```
    aquasec_security_scan:
    stage: security-scan
    ```

    **Test Jobs**: Tests are performed in the dev environment before deploying. Environment-specific variables such as `CA_CERTIFICATE`, `KUBE_API_SERVER`, and `SERVICE_ACCOUNT_TOKEN` are used for cluster authentication.

    ```
    test-dev-green:
    extends: .test-job-template
    variables:
        ENV_PATH: "regions/us-east-1/dev/green"
        CA_CERTIFICATE: $CA_CERTIFICATE_DEV_US_EAST_1_GREEN
        KUBE_API_SERVER: $KUBE_API_SERVER_DEV_US_EAST_1_GREEN
        SERVICE_ACCOUNT_TOKEN: $SERVICE_ACCOUNT_TOKEN_DEV_US_EAST_1_GREEN
    ```

    **Deploy MutatingWebhook Jobs**: Deploys the MutatingWebhook to the Kubernetes clusters using environment-specific configuration. These jobs are triggered when changes are made to the relevant folders or the CI file.These files are highlighted in the diagram in colour blue.

    ```
    us-east-1-dev-green:
        extends: .deploy-mutatingwebhook-template
        variables:
            ENV_PATH: "regions/us-east-1/dev/green"
            CA_CERTIFICATE: $CA_CERTIFICATE_DEV_US_EAST_1_GREEN
            KUBE_API_SERVER: $KUBE_API_SERVER_DEV_US_EAST_1_GREEN
            SERVICE_ACCOUNT_TOKEN: $SERVICE_ACCOUNT_TOKEN_DEV_US_EAST_1_GREEN
        only:
            changes: 
            - regions/us-east-1/dev/green/*
            - helm/k8s-annotation-mutatingwebhook/templates/configmap.yaml
            - .gitlab-ci.yml
            - common-steps-template.yml
            - service-account/serviceaccount.yaml
    ```

3. **Templates and Includes**

    This GitLab Pipeline includes several external templates for common operations, such as security scanning and linting. These templates are referenced from the devops/tecsys-gitlab-ci project.

    ```
    include:
      - /aquasec-security-scan/aquasec-security-scan.yml
      - local: "common-steps-template.yml"
    ```

4. **Variables**

    `KUBECONFIG`: Path to the Kubernetes config file, allowing the jobs to authenticate with the cluster.

    `AQUA_FULL_SCAN`: Indicates whether to perform a full security scan using AquaSec.

# Linux CLI Prerequisites

## Clone the k8s-annotation-mutatingwebhook GitLab Project

```
git clone https://gitlab.tecsysrd.cloud/briang/k8s-annotation-mutatingwebhook.git
```

## [Install helm](https://helm.sh/docs/intro/install/) on your Linux CLI

Helm is a Kubernetes deployment tool for automating creation, packaging, configuration, and deployment of applications and services to Kubernetes clusters.

```
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
chmod 700 get_helm.sh
./get_helm.sh
which helm
helm version
```

## Service Account setup for GitLab Pipeline

The K8s Service Account that the GitLab Pipeline requires to grant it permissions must exist before the GitLab Pipeline is run.  Therefore, this Service Account must be manually created from the Linux CLI using the following steps:

### Step 1 - Create mutatingwh namespace with correct annotations and labels

The Service Account is created in the `mutatingwh` namespace and, therefore, this namespace must be manually created using this command:

```
kubectl create ns mutatingwh && \
kubectl annotate namespace mutatingwh meta.helm.sh/release-name=k8s-annotation-mutatingwebhook meta.helm.sh/release-namespace=gitlab --overwrite && \
kubectl label namespace mutatingwh app.kubernetes.io/managed-by=Helm --overwrite
```

Check that the `mutatingwh` namespace has been successfully created with this command:

```
kubectl get ns mutatingwh -o yaml
```

### Step 2 - Clone the general-scripts repository

```
git clone https://gitlab.tecsysrd.cloud/ops/noc/general-scripts.git
```

In this repo is a directory called `gitlab` with a bash script named `set-gitlab-env-vars.sh`.  This script will create the necessary GitLab CI/CD environment variables.
You will need to modify this script before running it.  First, you will need to set the values of these variables found at the top of the script:

```
GITLAB_PROJECT_ID="" # The Project Id of the GitLab Project where these environment variables will be created, e.g. 23012
ENV=""               # K8s cluster environment, e.g. RD, DEV, NPRI, NPR, PRD
REGION=""            # AWS region of cluster, e.g. us-east-1 or ca-central-1
COLOR=""             # K8s cluster color, e.g. Blue, Green, etc
GITLAB_TOKEN=""      # Replace with your actual GitLab token
K8S_NAMESPACE=""     # Namespace for the Kubernetes service account, probably mutatingwh
```

Second, you will need to modify the path to the serviceaccount.yaml file which is currently set to `~/k8s-annotation-mutatingwebhook/service-account/serviceaccount.yaml`

Once that is done run the script and it will create these three GitLab CI/CD environment variables in the `k8s-annotation-mutatingwebhook` repository:

```
CA_CERTIFICATE_DEV_{ENV}_{REGION}_{COLOR}
KUBE_API_SERVER_{ENV}_{REGION}_{COLOR}
SERVICE_ACCOUNT_TOKEN_{ENV}_{REGION}_{COLOR}
```

The GitLab Pipeline is now ready to be run from the GitLab console.

# GitLab Pipeline Troubleshooting

**Pipeline Failures**: If you encounter issues, check GitLab's CI/CD logs for errors related to linting, security scans, or deployment steps.

**Aquasec Issues**: The R&D Security team manages Aquasec-related issues. For assistance, contact Sally Szeto. The following Aquasec job issue is linked to rate limiting on the ECR used by the scanner, and this has already been reported to the Security team.

![alt text](images/aquasec-issue.png)

# Gitlab Best Practices
This repository follows GitLab best practices to maintain a DRY (Don't Repeat Yourself) CI YAML file, particularly essential for managing multi-region environments. To reduce code duplication, we utilize mechanisms such as `includes` and `extends`. For more details, refer [Keeping Your Development Dry ](https://about.gitlab.com/blog/2023/01/03/keeping-your-development-dry/).

# Linux CLI Testing of MutatingWebhook After Successful Run of GitLab Pipeline

Ensure you are in the correct K8s context and then check the Helm installation by running the following command:
 
```
kubectl -n mutatingwh get all,cm,secret,sa,MutatingWebhookConfiguration,hpa,globalnetworkpolicies.crd.projectcalico.org -o wide
```

A correct installation should show these K8s resources:

* Pod,
* ReplicaSet,
* Deployment,
* HorizontalPodAutoscaler,
* Service,
* Secret,
* ServiceAccount,
* MutatingWebhookConfiguration, and
* GlobalNetworkPolicy

There are two Pod manifests in the test-pods subdirectory that will create a basic nginx in the default and mutatingwh namespace.  If you describe these Pods you will see the required annotations in the nginx Pod in the mutatingmh namespace.
Also, the testing can be performed just from the CLI using the following kubectl commands:

## Dev and RD Clusters

The Dev and RD clusters do not have customer namespaces. Therefore, the actual list of live namespaces cannot be used and we must create artificial namespaces to test against.  For the tests below to work the ConfigMap named `liveconfigmap` must contain the mutatingwh1 and mutatingwh3 namespaces.

```
kubectl create ns mutatingwh1
kubectl create ns mutatingwh2
kubectl create ns mutatingwh3

kubectl run nginx --image=nginx
kubectl run nginx --image=nginx -n mutatingwh1
kubectl run nginx --image=nginx -n mutatingwh3

kubectl get pod nginx -o yaml
...
metadata:
  annotations:

kubectl -n mutatingwh1 get pod nginx -o yaml
...
metadata:
  annotations:
    ad.datadoghq.com/tags: '{"env": "prd", "cluster_type": "blue", "namespace": "mcleod",
      "client_name": "mcleod", "client_environment": "default", "release": "N/A. No
      release name found", "live": "true", "service": "tecsys-elite-appnode", "role":
      "app", "kind": "Stateful", "region": "us-east-1"}'

kubectl -n mutatingwh3 get pod nginx -o yaml
...
metadata:
  annotations:
    ad.datadoghq.com/tags: '{"env": "prd", "cluster_type": "blue", "namespace": "mcleod",
      "client_name": "mcleod", "client_environment": "default", "release": "N/A. No
      release name found", "live": "true", "service": "tecsys-elite-appnode", "role":
      "app", "kind": "Stateful", "region": "us-east-1"}'
```

### JSON Formatted Annotations

For more readable output of the annotations use either of the two following command:

```
kubectl -n cloudtest get pod nginx -o json | jq '.metadata.annotations'
kubectl -n cloudtest get pod nginx -o jsonpath='{.metadata.annotations}' | jq
```

### Cleanup

```
kubectl delete ns mutatingwh3
kubectl delete ns mutatingwh2
kubectl delete ns mutatingwh1
```

## NPRi, NPR and Production Clusters

The actual customer namespaces exist in these clusters and, therefore, we must test against one of the customer namespaces in the `live-list.txt` found in the ConfigMap named `liveconfigmap`.  In the example below we test using the `cloudtest` namespace.

```
kubectl run nginx --image=nginx -n cloudtest --dry-run=server -o yaml
```

Check the annotations section of the output and confirm you see the correct annotations.  For instance, you should see annotations like these:

```
ad.datadoghq.com/tags: '{"env": "prd", "cluster_type": "blue", "namespace": "mcleod",
  "client_name": "mcleod", "client_environment": "default", "release": "N/A. No
  release name found", "live": "true", "service": "tecsys-elite-appnode", "role":
  "app", "kind": "Stateful", "region": "us-east-1"}'
```

### JSON Formatted Annotations

For more readable output of the annotations use either of the two following command:

```
kubectl -n cloudtest get pod nginx -o json | jq '.metadata.annotations'
kubectl -n cloudtest get pod nginx -o jsonpath='{.metadata.annotations}' | jq
```

#### Examples

Both of these examples produce the same output.

json example:

```
kubectl -n mcleod get pod default-tecsys-elite-appnode-0 -o json | jq '.metadata.annotations'
{
  "ad.datadoghq.com/tags": "{\"env\": \"prd\", \"cluster_type\": \"blue\", \"namespace\": \"mcleod\", \"client_name\": \"mcleod\", \"client_environment\": \"default\", \"release\": \"N/A. No release name found\", \"live\": \"true\", \"service\": \"tecsys-elite-appnode\", \"role\": \"app\", \"kind\": \"Stateful\", \"region\": \"us-east-1\"}",
  "admission.datadoghq.com/java-lib.version": "v1.0.0",
  "cluster-autoscaler.kubernetes.io/safe-to-evict-local-volumes": "datadog,datadog-auto-instrumentation,datadog-auto-instrumentation-etc",
  "istio.io/rev": "default",
  "kubectl.kubernetes.io/default-container": "tecsys-elite-appnode",
  "kubectl.kubernetes.io/default-logs-container": "tecsys-elite-appnode",
  "prometheus.io/path": "/stats/prometheus",
  "prometheus.io/port": "15020",
  "prometheus.io/scrape": "true",
  "sidecar.istio.io/status": "{\"initContainers\":[\"istio-init\"],\"containers\":[\"istio-proxy\"],\"volumes\":[\"workload-socket\",\"credential-socket\",\"workload-certs\",\"istio-envoy\",\"istio-data\",\"istio-podinfo\",\"istio-token\",\"istiod-ca-cert\"],\"imagePullSecrets\":null,\"revision\":\"default\"}"
}
```

jsonpath example:

```
kubectl -n mcleod get pod default-tecsys-elite-appnode-0 -o jsonpath='{.metadata.annotations}' | jq
{
  "ad.datadoghq.com/tags": "{\"env\": \"prd\", \"cluster_type\": \"blue\", \"namespace\": \"mcleod\", \"client_name\": \"mcleod\", \"client_environment\": \"default\", \"release\": \"N/A. No release name found\", \"live\": \"true\", \"service\": \"tecsys-elite-appnode\", \"role\": \"app\", \"kind\": \"Stateful\", \"region\": \"us-east-1\"}",
  "admission.datadoghq.com/java-lib.version": "v1.0.0",
  "cluster-autoscaler.kubernetes.io/safe-to-evict-local-volumes": "datadog,datadog-auto-instrumentation,datadog-auto-instrumentation-etc",
  "istio.io/rev": "default",
  "kubectl.kubernetes.io/default-container": "tecsys-elite-appnode",
  "kubectl.kubernetes.io/default-logs-container": "tecsys-elite-appnode",
  "prometheus.io/path": "/stats/prometheus",
  "prometheus.io/port": "15020",
  "prometheus.io/scrape": "true",
  "sidecar.istio.io/status": "{\"initContainers\":[\"istio-init\"],\"containers\":[\"istio-proxy\"],\"volumes\":[\"workload-socket\",\"credential-socket\",\"workload-certs\",\"istio-envoy\",\"istio-data\",\"istio-podinfo\",\"istio-token\",\"istiod-ca-cert\"],\"imagePullSecrets\":null,\"revision\":\"default\"}"
}
```

## List All Pods In All Namespaces Sorted By Creation Time

Check that this MutatingWebhook is not preventing new Pods from being created by running the following command:

```
kubectl get po -A --sort-by={metadata.creationTimestamp} --no-headers
```

Confirm Pods have been created after the MutatingWebhook was installed.

# Problem Troubleshooting

## Service and DNS Configuration

The webhook relies on the Kubernetes DNS service to resolve the service name (add-annotations-webhook-svc.mutatingwh.svc). If DNS is not properly configured or delayed, the webhook request might time out.

### Solutions

Verify that the service is reachable:

```
kubectl run test --rm -it --image=busybox -- /bin/sh
nslookup add-annotations-webhook-svc.mutatingwh.svc
```

or

```
kubectl run test --rm -it --image=busybox -- /bin/sh
nslookup add-annotations-webhook-svc.mutatingwh.svc.cluster.local
```

If the DNS resolution fails, check the kube-dns or coredns deployment.

## Network Policies or Admission Control

If your cluster uses network policies, admission controllers, or other security mechanisms, they might block communication between the API server and the webhook.

Here are some commands that will help with Calico GlobalNetworkPolicy.

```
kubectl get crds
kubectl get crds | grep networkpolicies
kubectl get globalnetworkpolicies.crd.projectcalico.org
kubectl explain globalnetworkpolicies.crd.projectcalico.org
kubectl get globalnetworkpolicies.crd.projectcalico.org ingress-allow-kubeapi-endpoint -o yaml
kubectl describe globalnetworkpolicies.crd.projectcalico.org mwh-network-policy
kubectl get globalnetworkpolicies.crd.projectcalico.org mwh-network-policy -o yaml
```

[Calico GlobalNetworkPolicy Documentation](https://docs.tigera.io/calico/latest/reference/resources/globalnetworkpolicy)

### Solutions

Ensure network policies allow traffic between the API server and the webhook service.

Test connectivity

```
kubectl run test --rm -it --image=busybox -- /bin/sh
wget https://add-annotations-webhook-svc.mutatingwh.svc:443/mutate --no-check-certificate
```

or

```
kubectl run test --rm -it --image=busybox -- /bin/sh
wget https://add-annotations-webhook-svc.mutatingwh.svc.cluster.local:443/mutate --no-check-certificate
```

Review the kube-apiserver logs for errors related to webhook communication.

## Debugging Steps

1. Check the logs of the running webhook pod

```
kubectl logs <webhook-pod-name>
```

2. Look for specific Python stack traces or timeout messages.

3. Increase logging verbosity for kube-apiserver and look for webhook-related errors.

# Uninstallation

All the K8s Annotation MutatingWebhook resources are uninstalled with the following Helm Chart command:

```
helm uninstall k8s-annotation-mutatingwebhook -n gitlab
```