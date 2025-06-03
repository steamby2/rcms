#!/bin/bash
# Script pour corriger le problème de connexion Logstash
# Le collecteur fonctionne mais ne peut pas se connecter à Logstash
# Auteur: Arthur

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    local status=$1
    local message=$2
    case $status in
        "OK") echo -e "${GREEN}✓ $message${NC}" ;;
        "WARNING") echo -e "${YELLOW}⚠ $message${NC}" ;;
        "ERROR") echo -e "${RED}✗ $message${NC}" ;;
        "INFO") echo -e "${BLUE}ℹ $message${NC}" ;;
    esac
}

echo "=== CORRECTION PROBLÈME LOGSTASH ==="
print_status "ERROR" "PROBLÈME IDENTIFIÉ: Connection refused vers Logstash"
print_status "INFO" "Le collecteur fonctionne mais Logstash n'écoute pas sur le port 5044"

# 1. Diagnostic du problème Logstash
echo ""
echo "1. DIAGNOSTIC LOGSTASH"
echo "======================"

# Vérifier l'état de Logstash
logstash_status=$(docker-compose ps logstash | grep -v "Name" | awk '{print $4}' || echo "unknown")
print_status "INFO" "État Logstash: $logstash_status"

# Vérifier les logs Logstash
echo ""
echo "Dernières erreurs Logstash:"
docker-compose logs logstash | grep -i "error\|exception\|failed" | tail -5 || echo "Aucune erreur trouvée"

# Vérifier si le port 5044 est exposé
echo ""
echo "Ports Logstash exposés:"
docker-compose ps logstash | grep -o "0.0.0.0:[0-9]*" || echo "Aucun port trouvé"

# 2. Corriger la configuration Logstash
echo ""
echo "2. CORRECTION CONFIGURATION LOGSTASH"
echo "===================================="

# Créer une configuration Logstash simplifiée qui fonctionne
print_status "INFO" "Création d'une configuration Logstash simplifiée..."

cat > vm4_logstash/pipeline/dme_pipeline.conf << 'EOF'
input {
  # TCP Input pour recevoir les données du collecteur
  tcp {
    port => 5044
    codec => json_lines
    type => "dme_metrics"
  }
  
  # Input de test pour vérifier que Logstash fonctionne
  generator {
    message => "Test Logstash heartbeat"
    count => 1
    type => "heartbeat"
  }
}

filter {
  if [type] == "dme_metrics" {
    # Traitement simple des métriques DME
    mutate {
      add_field => {
        "environment" => "production"
        "application" => "dme_monitoring"
        "processed_by" => "logstash"
        "processed_at" => "%{@timestamp}"
      }
    }
    
    # Validation des données
    if ![metrics] {
      mutate {
        add_tag => ["_data_error"]
        add_field => { "error_reason" => "missing_metrics_field" }
      }
    }
  }
  
  if [type] == "heartbeat" {
    mutate {
      add_field => {
        "service" => "logstash"
        "status" => "alive"
      }
    }
  }
}

output {
  # Sortie vers Elasticsearch
  if [type] == "dme_metrics" {
    elasticsearch {
      hosts => ["elasticsearch:9200"]
      user => "elastic"
      password => "SuperAdmin123!"
      index => "rcms-dme-%{+YYYY.MM.dd}"
      document_type => "_doc"
    }
  }
  
  # Sortie heartbeat vers un index séparé
  if [type] == "heartbeat" {
    elasticsearch {
      hosts => ["elasticsearch:9200"]
      user => "elastic"
      password => "SuperAdmin123!"
      index => "logstash-heartbeat-%{+YYYY.MM.dd}"
      document_type => "_doc"
    }
  }
  
  # Debug: tout vers stdout
  stdout {
    codec => rubydebug
  }
}
EOF

print_status "OK" "Configuration Logstash simplifiée créée"

# 3. Créer une configuration Logstash.yml simple
echo ""
print_status "INFO" "Mise à jour de logstash.yml..."

cat > vm4_logstash/config/logstash.yml << 'EOF'
http.host: "0.0.0.0"
http.port: 9600

path.config: /usr/share/logstash/pipeline
config.reload.automatic: true
config.reload.interval: 3s

pipeline.workers: 2
pipeline.batch.size: 125
pipeline.batch.delay: 50

# Désactiver X-Pack monitoring pour simplifier
xpack.monitoring.enabled: false

# Log level pour debug
log.level: info
path.logs: /var/log/logstash
EOF

print_status "OK" "logstash.yml mis à jour"

# 4. Redémarrer Logstash
echo ""
echo "3. REDÉMARRAGE LOGSTASH"
echo "======================="

print_status "INFO" "Arrêt de Logstash..."
docker-compose stop logstash

print_status "INFO" "Suppression du conteneur Logstash..."
docker-compose rm -f logstash

print_status "INFO" "Redémarrage de Logstash..."
docker-compose up -d logstash

# 5. Attendre et vérifier
echo ""
echo "4. VÉRIFICATION POST-REDÉMARRAGE"
echo "================================="

print_status "INFO" "Attente 30 secondes pour le démarrage de Logstash..."
sleep 30

# Vérifier l'état de Logstash
new_status=$(docker-compose ps logstash | grep -v "Name" | awk '{print $4}' || echo "unknown")
print_status "INFO" "Nouvel état Logstash: $new_status"

# Tester l'API Logstash
if curl -s -f http://localhost:9600/_node >/dev/null 2>&1; then
    print_status "OK" "API Logstash accessible"
else
    print_status "WARNING" "API Logstash pas encore accessible"
fi

# Vérifier les logs récents
echo ""
echo "Logs Logstash récents:"
docker-compose logs logstash | tail -10

# 6. Test de connectivité
echo ""
echo "5. TEST DE CONNECTIVITÉ"
echo "======================="

# Tester si le port 5044 est accessible depuis le collecteur
print_status "INFO" "Test de connectivité port 5044..."

# Redémarrer le collecteur pour qu'il retente la connexion
print_status "INFO" "Redémarrage du collecteur..."
docker-compose restart data_collector

print_status "INFO" "Attente 10 secondes..."
sleep 10

# Vérifier les nouveaux logs du collecteur
echo ""
echo "Nouveaux logs du collecteur:"
docker-compose logs data_collector | tail -5

# 7. Instructions finales
echo ""
echo "6. INSTRUCTIONS FINALES"
echo "======================="

print_status "INFO" "Actions à suivre:"
echo "1. Attendez 3-5 minutes pour voir les nouveaux logs du collecteur"
echo "2. Vérifiez les logs avec: docker-compose logs data_collector | tail -10"
echo "3. Si 'Connection refused' disparaît, les données vont remonter"
echo "4. Vérifiez dans Elasticsearch: curl -u 'elastic:SuperAdmin123!' 'http://localhost:9200/_cat/indices'"
echo "5. Si des indices rcms-dme-* apparaissent, créez l'index pattern dans Kibana"

# 8. Script de surveillance
echo ""
print_status "INFO" "Création d'un script de surveillance..."

cat > monitor-flow.sh << 'EOF'
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
EOF

chmod +x monitor-flow.sh
print_status "OK" "Script de surveillance créé: ./monitor-flow.sh"

echo ""
print_status "OK" "CORRECTION TERMINÉE"
print_status "INFO" "Surveillez maintenant avec: ./monitor-flow.sh"