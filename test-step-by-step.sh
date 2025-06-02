#!/bin/bash
echo "=== Test de démarrage par étapes ==="

echo "1. Test Elasticsearch seul..."
docker-compose up -d elasticsearch
echo "Attente 30 secondes pour Elasticsearch..."
sleep 30
docker-compose logs elasticsearch
echo ""

echo "2. Test de l'API Elasticsearch..."
curl -f http://localhost:9200/_cluster/health || echo "Elasticsearch pas encore prêt"
echo ""

echo "3. Ajout de Kibana..."
docker-compose up -d kibana
echo "Attente 60 secondes pour Kibana..."
sleep 60
docker-compose logs kibana
echo ""

echo "4. Test de l'API Kibana..."
curl -f http://localhost:5601/api/status || echo "Kibana pas encore prêt"
echo ""

echo "5. Ajout de Logstash..."
docker-compose up -d logstash
echo "Attente 30 secondes pour Logstash..."
sleep 30
docker-compose logs logstash
echo ""

echo "6. Démarrage des services DME..."
docker-compose up -d dme_simulator data_collector
echo "Attente 15 secondes..."
sleep 15

echo "7. Test final des services..."
echo "Services actifs :"
docker-compose ps

echo ""
echo "Test API DME :"
curl -s http://localhost:5000/health | jq '.' || echo "Service DME non accessible"

echo ""
echo "Test Elasticsearch :"
curl -s http://localhost:9200/_cluster/health | jq '.' || echo "Elasticsearch non accessible"

echo ""
echo "=== Fin du test par étapes ==="
