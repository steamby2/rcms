#!/bin/bash
cd vm3_elasticsearch/certs
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout elastic-certificates.key \
    -out elastic-certificates.crt \
    -subj "/C=FR/ST=France/L=Paris/O=RCMS/OU=Test/CN=elasticsearch"

# Créer le fichier p12
openssl pkcs12 -export -out elastic-certificates.p12 \
    -inkey elastic-certificates.key \
    -in elastic-certificates.crt \
    -passout pass:
