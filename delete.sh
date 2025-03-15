kubectl delete -f manifests/mutatingwebhookconfiguration.yaml
kubectl delete -f manifests/hpa.yaml
kubectl delete -f manifests/service.yaml
kubectl delete -f manifests/deployment.yaml
kubectl delete -f manifests/secrets.yaml
kubectl delete -f manifests/configmap.yaml
kubectl delete ns mutatingwh