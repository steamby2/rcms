#!/bin/bash
echo "=== TEST COMPLET DU FLUX DE DONNÉES ==="

echo "1. Attente du démarrage des services (60s)..."
sleep 5

echo "2. Test API DME..."
curl -s http://localhost:5000/health | jq '.'

echo "3. Test données DME..."
curl -s http://localhost:5000/all | jq '.data | keys | length'

echo "4. Attente collecte (30s)..."
sleep 30

echo "5. Test Elasticsearch avec authentification..."
curl -u "elastic:SuperAdmin123!" -s "http://localhost:9200/_cluster/health" | jq '.'

echo "6. Vérification des indices..."
curl -u "elastic:SuperAdmin123!" -s "http://localhost:9200/_cat/indices"

echo "7. Recherche dans les données RCMS..."
curl -u "elastic:SuperAdmin123!" -s "http://localhost:9200/rcms-dme-*/_search?size=1" | jq '.hits.total'

echo "8. Test Kibana..."
curl -s "http://localhost:5601/api/status" | jq '.status.overall.state'

echo "=== FIN DU TEST ==="
