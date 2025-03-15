keydir="certificates"
cd "$keydir"

# Generate a Private Key for the CA
openssl genrsa -out ca.key 2048

# Create a Self-Signed Certificate for the CA
openssl req -x509 -new -nodes -key ca.key -subj "/CN=MutatingWebhookCA" -days 365 -out ca.crt

# Generate the Webhook Server Private Key
openssl genrsa -out webhook-server.key 2048

# Create a Certificate Signing Request (CSR) for the Webhook Server
openssl req -new -key webhook-server.key -subj "/CN=add-annotations-webhook-svc.mutatingwh.svc" -out webhook-server.csr

# Sign the Webhook Server Certificate with the CA
openssl x509 -req -in webhook-server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out webhook-server.crt -days 365 -extfile <(echo "subjectAltName=DNS:add-annotations-webhook-svc.mutatingwh.svc")
