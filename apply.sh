kubectl create ns mutatingwh
kubectl apply -f manifests/configmap.yaml
kubectl apply -f manifests/secrets.yaml
kubectl apply -f manifests/deployment.yaml
kubectl apply -f manifests/service.yaml
kubectl apply -f manifests/hpa.yaml
kubectl apply -f manifests/mutatingwebhookconfiguration.yaml