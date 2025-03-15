# Overview

This document explains how to setup the standalone Helm Chart package that deploys the K8s Annotation MutatingWebhook solution using Helm templates and values file.

# Prerequisites

## [Install helm](https://helm.sh/docs/intro/install/)

Helm is a Kubernetes deployment tool for automating creation, packaging, configuration, and deployment of applications and services to Kubernetes clusters.

```
curl -fsSL -o get_helm.sh https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3
chmod 700 get_helm.sh
./get_helm.sh
which helm
helm version
```

# Helm Project Setup Background

The Helm Chart structure for this project was created using a command that is typically only executed once, per project. This command is executed at the beginning of the Helm project setup,
in order to create the correct Helm project directory structure with required manifest files.  This command is only shown below for education puproses and should not be run if using the cloned repository.

**IMPORTANT: DO NOT RUN THIS COMMAND ON THE CLONED REPO BECAUSE IT WILL OVERWRITE ALL MANIFEST FILES WITH DEFAULT VERSIONS**

```
helm create k8s-annotation-mutatingwebhook
```

# Validation of Helm Templates and Values

After running the previous command, the Chart.yaml, values.yaml and other manifest files in the /templates directory were modified for this project.

Those K8s manifests files in the /templates directory can be validated using the following command:

```
helm template k8s-annotation-mutatingwebhook --debug
```

# Installation

The K8s MutatingWebhook resources can be installed with the following Helm Chart command:

```
helm install k8s-annotation-mutatingwebhook k8s-annotation-mutatingwebhook
```

# Upgrade

If a manifest file changes, perhaps the number of replicas in the deployment or the values in a ConfigMap then an upgrade needs to be performed.  The K8s MutatingWebhook resources can be upgraded with the following Helm Chart command:

```
helm upgrade k8s-annotation-mutatingwebhook k8s-annotation-mutatingwebhook
```

# Testing

Check the helm installation by running the following command:
 
```
kubectl -n mutatingwh get all,cm,secret,MutatingWebhookConfiguration,hpa,globalnetworkpolicies.crd.projectcalico.org -o wide
```

A correct installation should show these K8s resources:

* Pod,
* ReplicaSet,
* Deployment,
* HorizontalPodAutoscaler,
* Service,
* Secret,
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

All the K8s MutatingWebhook resources are uninstalled with the following Helm Chart command:

```
helm uninstall k8s-annotation-mutatingwebhook
```