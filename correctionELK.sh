#!/bin/bash
# Script de correction finale pour ELK Stack RCMS_Test
# Corrige les problèmes de permissions, variables et SSL
# Auteur: Arthur

set -e

echo "=== Correction finale ELK Stack ==="

# 1. Arrêter tous les services
echo "1. Arrêt de tous les services..."
docker-compose down 2>/dev/null || true

# 2. Corriger les permissions des secrets
echo "2. Correction des permissions des secrets..."
chmod 600 secrets/elastic_password.txt
chmod 600 secrets/kibana_encryption_key.txt
echo "  ✓ Permissions des secrets corrigées (600)"

# 3. Créer un docker-compose.yml simplifié sans SSL
echo "3. Création d'un docker-compose.yml simplifié..."
cat > docker-compose.yml << 'EOF'
version: '3.8'

services:
  # VM1: Simulateur DME
  dme_simulator:
    build:
      context: ./vm1_dme_simulator
      dockerfile: Dockerfile
    container_name: rcms_dme_simulator
    restart: unless-stopped
    ports:
      - "161:161/udp"
      - "5000:5000"
    volumes:
      - ./logs/dme_simulator:/app/logs
    environment:
      - SNMP_USER=dmeuser
      - SNMP_AUTH_PROTOCOL=SHA
      - SNMP_AUTH_PASSWORD=authpassword
      - SNMP_PRIV_PROTOCOL=AES
      - SNMP_PRIV_PASSWORD=privpassword
      - PORT=5000
      - HOST=0.0.0.0
    networks:
      - rcms_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 20s

  # VM2: Collecteur de données
  data_collector:
    build:
      context: ./vm2_data_collector
      dockerfile: Dockerfile
    container_name: rcms_data_collector
    restart: unless-stopped
    depends_on:
      - dme_simulator
    volumes:
      - ./data:/app/data
      - ./logs/data_collector:/app/logs
    environment:
      - DME_SIMULATOR_URL=http://dme_simulator:5000
      - COLLECTION_INTERVAL=180
      - OUTPUT_FILE=/app/data/dme_data.csv
      - LOGSTASH_ENABLED=false
    networks:
      - rcms_network

  # VM3: Elasticsearch (sans sécurité pour simplifier)
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.14.0
    container_name: rcms_elasticsearch
    restart: unless-stopped
    ports:
      - "9200:9200"
      - "9300:9300"
    volumes:
      - elasticsearch_data:/usr/share/elasticsearch/data
      - elasticsearch_logs:/usr/share/elasticsearch/logs
    environment:
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
      - discovery.type=single-node
      - xpack.security.enabled=false
      - path.logs=/usr/share/elasticsearch/logs
      - bootstrap.memory_lock=false
    ulimits:
      memlock:
        soft: -1
        hard: -1
    networks:
      - rcms_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9200/_cluster/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # VM4: Logstash (simplifié sans SSL)
  logstash:
    image: docker.elastic.co/logstash/logstash:7.14.0
    container_name: rcms_logstash
    restart: unless-stopped
    depends_on:
      - elasticsearch
    ports:
      - "5044:5044"
      - "9600:9600"
    volumes:
      - ./vm4_logstash/pipeline:/usr/share/logstash/pipeline:ro
      - ./vm4_logstash/config/logstash.yml:/usr/share/logstash/config/logstash.yml:ro
      - logstash_logs:/var/log/logstash
    environment:
      - ELASTIC_USERNAME=elastic
      - ELASTIC_PASSWORD=changeme
    networks:
      - rcms_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9600/_node"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  # VM5: Kibana (simplifié sans SSL)
  kibana:
    image: docker.elastic.co/kibana/kibana:7.14.0
    container_name: rcms_kibana
    restart: unless-stopped
    depends_on:
      - elasticsearch
    ports:
      - "5601:5601"
    volumes:
      - kibana_logs:/var/log/kibana
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200
      - XPACK_ENCRYPTEDSAVEDOBJECTS_ENCRYPTIONKEY=ChangeMe123456789012345678901234567890
      - SERVER_NAME=rcms-kibana
      - SERVER_HOST=0.0.0.0
      - I18N_LOCALE=fr
    networks:
      - rcms_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5601/api/status"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 120s

networks:
  rcms_network:
    driver: bridge
    ipam:
      driver: default
      config:
        - subnet: 172.20.0.0/16

volumes:
  elasticsearch_data:
    driver: local
  elasticsearch_logs:
    driver: local
  logstash_logs:
    driver: local
  kibana_logs:
    driver: local
EOF
echo "  ✓ docker-compose.yml simplifié créé (sans SSL)"

# 4. Créer une configuration Logstash simplifiée
echo "4. Création d'une configuration Logstash simplifiée..."
cat > vm4_logstash/pipeline/dme_pipeline.conf << 'EOF'
input {
  # Réception des données du collecteur DME (sans SSL)
  tcp {
    port => 5044
    codec => json
    type => "dme_metrics"
  }
  
  # Surveillance des fichiers de logs du système
  file {
    path => "/var/log/dme_collector.log"
    start_position => "beginning"
    type => "collector_logs"
  }
}

filter {
  if [type] == "dme_metrics" {
    # Traitement des métriques DME
    date {
      match => [ "@timestamp", "ISO8601" ]
      target => "@timestamp"
    }
    
    # Ajout de métadonnées
    mutate {
      add_field => {
        "environment" => "production"
        "application" => "dme_monitoring"
      }
    }
    
    # Conversion des types de données pour les métriques principales
    mutate {
      convert => {
        "metrics.mtuExecTXPBDelayCurrentValue-0" => "integer"
        "metrics.mtuExecTXPBDelayCurrentValue-3" => "integer"
        "metrics.mtuExecTXPBTransmittedPowerCurrentValue-0" => "integer"
        "metrics.mtuExecTXPBTransmittedPowerCurrentValue-3" => "integer"
        "metrics.mtuExecTXPBEfficiency-0" => "integer"
        "metrics.mtuExecTXPBEfficiency-3" => "integer"
        "metrics.mtuExecRadiatedPowerCurrentValue-0" => "integer"
        "metrics.mtuExecRadiatedPowerCurrentValue-3" => "integer"
        "metrics.mtuExecTransmissionRate-0" => "integer"
        "metrics.mtuExecTransmissionRate-3" => "integer"
      }
    }
  }
  
  if [type] == "collector_logs" {
    # Traitement des logs du collecteur
    grok {
      match => { "message" => "%{TIMESTAMP_ISO8601:timestamp} - %{WORD:log_name} - %{LOGLEVEL:log_level} - %{GREEDYDATA:log_message}" }
    }
    
    # Classification des logs
    if [log_level] == "ERROR" or [log_level] == "CRITICAL" {
      mutate {
        add_field => { "priority" => "high" }
      }
    } else if [log_level] == "WARNING" {
      mutate {
        add_field => { "priority" => "medium" }
      }
    } else {
      mutate {
        add_field => { "priority" => "low" }
      }
    }
  }
}

output {
  # Envoi des données à Elasticsearch (sans SSL)
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    index => "rcms-dme-%{+YYYY.MM.dd}"
  }
  
  # Journalisation des événements de traitement
  stdout {
    codec => rubydebug
  }
}
EOF
echo "  ✓ Configuration Logstash simplifiée créée"

# 5. Créer une version simplifiée du collecteur sans Logstash
echo "5. Mise à jour du collecteur pour désactiver Logstash..."
cat > vm2_data_collector/requirements.txt << 'EOF'
requests==2.26.0
python-dotenv==0.19.0
EOF
echo "  ✓ Requirements collecteur simplifiés"

# 6. Test de démarrage par étapes
echo "6. Création d'un script de test par étapes..."
cat > test-step-by-step.sh << 'EOF'
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
EOF

chmod +x test-step-by-step.sh
echo "  ✓ Script de test par étapes créé"

# 7. Nettoyer et reconstruire
echo "7. Nettoyage et reconstruction..."
docker system prune -f 2>/dev/null || true
echo "  ✓ Images nettoyées"

echo ""
echo "=== Correction finale terminée ==="
echo ""
echo "Configuration simplifiée appliquée :"
echo "✓ Elasticsearch : Sans sécurité/SSL"
echo "✓ Kibana : Configuration directe sans secrets"
echo "✓ Logstash : Pipeline simplifié sans SSL"
echo "✓ Collecteur : Logstash désactivé"
echo "✓ Permissions : Secrets corrigés"
echo ""
echo "Étapes suivantes :"
echo "1. Testez par étapes : ./test-step-by-step.sh"
echo "2. Ou démarrage direct : docker-compose up -d"
echo "3. Accès Kibana : http://localhost:5601"
echo "4. Accès Elasticsearch : http://localhost:9200"
echo "5. API DME : http://localhost:5000"
echo ""
echo "Note: Cette configuration est optimisée pour le développement."
echo "En production, réactivez la sécurité et SSL."
EOF