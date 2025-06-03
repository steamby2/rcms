#!/bin/bash
echo "=== SURVEILLANCE FLUX DE DONNÉES RCMS ==="

echo "1. État des services:"
docker-compose ps

echo ""
echo "2. Derniers logs collecteur:"
docker-compose logs data_collector | tail -3

echo ""
echo "3. Test Logstash API:"
curl -s http://localhost:9600/_node | jq '.pipeline' 2>/dev/null || echo "API Logstash non accessible"

echo ""
echo "4. Indices Elasticsearch:"
curl -u "elastic:SuperAdmin123!" -s "http://localhost:9200/_cat/indices" | grep -E "(rcms|logstash)" || echo "Aucun indice RCMS trouvé"

echo ""
echo "5. Comptage documents RCMS:"
curl -u "elastic:SuperAdmin123!" -s "http://localhost:9200/rcms-dme-*/_count" 2>/dev/null | jq '.count' || echo "0"

echo ""
echo "=== Exécutez ce script toutes les 2 minutes pour surveiller ==="
