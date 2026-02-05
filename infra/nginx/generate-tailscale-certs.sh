#!/bin/bash
# Generate HTTPS certificates using Tailscale
# Run this after setting up Tailscale: sudo tailscale up

set -e

CERT_DIR="$(dirname "$0")/certs"
mkdir -p "$CERT_DIR"

# Get the Tailscale machine name (e.g., "my-machine.tail1234.ts.net")
TAILSCALE_FQDN=$(tailscale status --json | jq -r '.Self.DNSName' | sed 's/\.$//')

if [ -z "$TAILSCALE_FQDN" ] || [ "$TAILSCALE_FQDN" = "null" ]; then
    echo "Error: Could not get Tailscale FQDN. Make sure Tailscale is running."
    echo "Run: sudo tailscale up"
    exit 1
fi

echo "Generating certificates for: $TAILSCALE_FQDN"

# Generate the certificate
sudo tailscale cert --cert-file "$CERT_DIR/cert.pem" --key-file "$CERT_DIR/key.pem" "$TAILSCALE_FQDN"

# Fix permissions so nginx can read them
sudo chmod 644 "$CERT_DIR/cert.pem"
sudo chmod 644 "$CERT_DIR/key.pem"

echo ""
echo "Certificates generated successfully!"
echo "  Cert: $CERT_DIR/cert.pem"
echo "  Key:  $CERT_DIR/key.pem"
echo ""
echo "Your HTTPS URL: https://$TAILSCALE_FQDN"
echo ""
echo "Restart nginx to apply: sudo docker-compose restart nginx"
