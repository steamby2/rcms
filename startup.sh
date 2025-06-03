#!/bin/bash
# Script pour configurer la sécurité et créer un compte super admin
# Résout aussi le problème d'envoi des données vers Elasticsearch
# Auteur: Arthur

set -e

echo "=== CONFIGURATION SÉCURITÉ ET CORRECTION FLUX DE DONNÉES ==="

# Couleurs pour l'affichage
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

# 1. Arrêter les services
echo "1. Arrêt des services..."
docker-compose down

# 2. Corriger le docker-compose.yml pour activer Logstash ET la sécurité
echo "2. Configuration complète avec sécurité activée..."
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

  # VM2: Collecteur de données (LOGSTASH ACTIVÉ)
  data_collector:
    build:
      context: ./vm2_data_collector
      dockerfile: Dockerfile
    container_name: rcms_data_collector
    restart: unless-stopped
    depends_on:
      - dme_simulator
      - logstash
    volumes:
      - ./data:/app/data
      - ./logs/data_collector:/app/logs
    environment:
      - DME_SIMULATOR_URL=http://dme_simulator:5000
      - COLLECTION_INTERVAL=180
      - OUTPUT_FILE=/app/data/dme_data.csv
      - LOGSTASH_ENABLED=true
      - LOGSTASH_HOST=logstash
      - LOGSTASH_PORT=5044
    networks:
      - rcms_network

  # VM3: Elasticsearch (avec sécurité)
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
      - xpack.security.enabled=true
      - xpack.security.authc.api_key.enabled=true
      - ELASTIC_PASSWORD=SuperAdmin123!
      - path.logs=/usr/share/elasticsearch/logs
      - bootstrap.memory_lock=false
    ulimits:
      memlock:
        soft: -1
        hard: -1
    networks:
      - rcms_network
    healthcheck:
      test: ["CMD", "curl", "-u", "elastic:SuperAdmin123!", "-f", "http://localhost:9200/_cluster/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  # VM4: Logstash (configuration corrigée)
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
      - ELASTIC_PASSWORD=SuperAdmin123!
    networks:
      - rcms_network
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9600/_node"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  # VM5: Kibana (avec authentification)
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
      - ELASTICSEARCH_USERNAME=elastic
      - ELASTICSEARCH_PASSWORD=SuperAdmin123!
      - XPACK_ENCRYPTEDSAVEDOBJECTS_ENCRYPTIONKEY=ChangeMe123456789012345678901234567890
      - XPACK_SECURITY_ENABLED=true
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
print_status "OK" "docker-compose.yml mis à jour avec sécurité"

# 3. Créer une configuration Logstash corrigée
echo "3. Configuration du pipeline Logstash..."
cat > vm4_logstash/pipeline/dme_pipeline.conf << 'EOF'
input {
  # Réception des données du collecteur DME (sans SSL pour simplifier)
  tcp {
    port => 5044
    codec => json_lines
    type => "dme_metrics"
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
        "source" => "rcms_simulator"
      }
    }
    
    # S'assurer que les métriques existent
    if [metrics] {
      # Conversion des types de données pour les métriques principales
      ruby {
        code => "
          metrics = event.get('metrics')
          if metrics.is_a?(Hash)
            metrics.each do |key, value|
              if value.is_a?(String) && value.match(/^\d+$/)
                event.set('[metrics][' + key + ']', value.to_i)
              elsif value.is_a?(Numeric)
                event.set('[metrics][' + key + ']', value)
              end
            end
          end
        "
      }
      
      # Calcul de métriques dérivées simples
      if [metrics][mtuExecTXPBDelayCurrentValue-0] and [metrics][mtuExecTXPBDelayCurrentValue-3] {
        ruby {
          code => "
            delay0 = event.get('[metrics][mtuExecTXPBDelayCurrentValue-0]')
            delay3 = event.get('[metrics][mtuExecTXPBDelayCurrentValue-3]')
            if delay0.is_a?(Numeric) && delay3.is_a?(Numeric)
              event.set('[metrics][delay_diff]', (delay3 - delay0).abs)
            end
          "
        }
      }
    }
  }
}

output {
  # Envoi des données à Elasticsearch avec authentification
  elasticsearch {
    hosts => ["elasticsearch:9200"]
    user => "${ELASTIC_USERNAME}"
    password => "${ELASTIC_PASSWORD}"
    index => "rcms-dme-%{+YYYY.MM.dd}"
    template_name => "rcms-dme"
    template_pattern => "rcms-dme-*"
    template_overwrite => true
    template => {
      "index_patterns" => ["rcms-dme-*"],
      "settings" => {
        "number_of_shards" => 1,
        "number_of_replicas" => 0
      },
      "mappings" => {
        "properties" => {
          "@timestamp" => { "type" => "date" },
          "metrics" => { "type" => "object" },
          "environment" => { "type" => "keyword" },
          "application" => { "type" => "keyword" },
          "source" => { "type" => "keyword" }
        }
      }
    }
  }
  
  # Debug: journalisation sur stdout
  stdout {
    codec => rubydebug {
      metadata => true
    }
  }
  
  # Sauvegarde en cas de problème Elasticsearch
  file {
    path => "/var/log/logstash/rcms-backup-%{+YYYY-MM-dd}.log"
    codec => json_lines
  }
}
EOF
print_status "OK" "Pipeline Logstash configuré"

# 4. Mettre à jour le collecteur pour avoir des logs détaillés
echo "4. Mise à jour du collecteur avec logs détaillés..."
cat > vm2_data_collector/dme_collector.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Collecteur de données DME avec logs détaillés et envoi Logstash
Auteur: arthur
"""

import os
import time
import csv
import json
import logging
import requests
from datetime import datetime
import socket

# Configuration du logging détaillé
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/app/logs/dme_collector.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("dme_collector")

class Config:
    DME_SIMULATOR_URL = os.environ.get("DME_SIMULATOR_URL", "http://dme_simulator:5000")
    COLLECTION_INTERVAL = int(os.environ.get("COLLECTION_INTERVAL", 180))
    OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "/app/data/dme_data.csv")
    LOGSTASH_ENABLED = os.environ.get("LOGSTASH_ENABLED", "false").lower() == "true"
    LOGSTASH_HOST = os.environ.get("LOGSTASH_HOST", "logstash")
    LOGSTASH_PORT = int(os.environ.get("LOGSTASH_PORT", 5044))
    TIMEOUT = int(os.environ.get("TIMEOUT", 10))

class DMECollector:
    def __init__(self):
        self.config = Config()
        self.session = requests.Session()
        self.headers = {
            "User-Agent": "DME-Collector/1.0",
            "Accept": "application/json"
        }
        self.column_names = [
            "Timestamp",
            "mtuExecTXPADelayCurrentValue-0",
            "mtuExecTXPBDelayCurrentValue-0", 
            "mtuExecTXPADelayCurrentValue-3",
            "mtuExecTXPBDelayCurrentValue-3",
            "mtuExecTXPAPulsePairSpacing-0",
            "mtuExecTXPBPulsePairSpacing-0",
            "mtuExecTXPAPulsePairSpacing-3", 
            "mtuExecTXPBPulsePairSpacing-3",
            "mtuExecTXPATransmittedPowerCurrentValue-0",
            "mtuExecTXPBTransmittedPowerCurrentValue-0",
            "mtuExecTXPATransmittedPowerCurrentValue-3",
            "mtuExecTXPBTransmittedPowerCurrentValue-3",
            "mtuExecTXPAEfficiency-0",
            "mtuExecTXPBEfficiency-0",
            "mtuExecTXPAEfficiency-3",
            "mtuExecTXPBEfficiency-3",
            "mtuExecTXPATxFreqError-0",
            "mtuExecTXPBTxFreqError-0",
            "mtuExecTXPATxFreqError-3",
            "mtuExecTXPBTxFreqError-3",
            "mtuExecRadiatedPowerCurrentValue-0",
            "mtuExecRadiatedPowerCurrentValue-3",
            "mtuExecTransmissionRate-0",
            "mtuExecTransmissionRate-3",
            "mtuExecIdentStatus-0",
            "mtuExecIdentStatus-3"
        ]
        self._initialize_output_file()
        
        logger.info(f"Collecteur initialisé:")
        logger.info(f"  - URL Simulateur: {self.config.DME_SIMULATOR_URL}")
        logger.info(f"  - Intervalle: {self.config.COLLECTION_INTERVAL}s")
        logger.info(f"  - Logstash activé: {self.config.LOGSTASH_ENABLED}")
        logger.info(f"  - Logstash: {self.config.LOGSTASH_HOST}:{self.config.LOGSTASH_PORT}")
    
    def _initialize_output_file(self):
        """Initialise le fichier de sortie avec les en-têtes si nécessaire"""
        file_exists = os.path.isfile(self.config.OUTPUT_FILE)
        
        if not file_exists:
            try:
                os.makedirs(os.path.dirname(self.config.OUTPUT_FILE), exist_ok=True)
                with open(self.config.OUTPUT_FILE, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile, delimiter='\t')
                    writer.writerow(self.column_names)
                logger.info(f"Fichier CSV initialisé: {self.config.OUTPUT_FILE}")
            except Exception as e:
                logger.error(f"Erreur initialisation CSV: {str(e)}")
                raise
    
    def collect_data(self):
        """Collecte les données du simulateur DME"""
        try:
            url = f"{self.config.DME_SIMULATOR_URL}/all"
            logger.debug(f"Requête vers: {url}")
            
            response = self.session.get(
                url,
                headers=self.headers,
                timeout=self.config.TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info(f"Données collectées: {len(data.get('data', {}))} métriques")
                logger.debug(f"Données: {data}")
                return data
            else:
                logger.error(f"Erreur HTTP {response.status_code}: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Erreur collecte: {str(e)}")
            return None
    
    def format_data(self, data):
        """Formate les données pour CSV"""
        if not data or "data" not in data:
            return None
        
        dme_data = data["data"]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-4]
        
        row = [timestamp]
        for column in self.column_names[1:]:
            row.append(dme_data.get(column, 0))
        
        return row
    
    def save_to_csv(self, row):
        """Enregistre dans le fichier CSV"""
        if not row:
            return False
        
        try:
            with open(self.config.OUTPUT_FILE, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter='\t')
                writer.writerow(row)
            logger.info(f"Données CSV sauvegardées")
            return True
        except Exception as e:
            logger.error(f"Erreur sauvegarde CSV: {str(e)}")
            return False
    
    def send_to_logstash(self, data):
        """Envoie les données à Logstash avec gestion d'erreurs détaillée"""
        if not self.config.LOGSTASH_ENABLED:
            logger.debug("Logstash désactivé, envoi ignoré")
            return
        
        if not data:
            logger.warning("Pas de données à envoyer à Logstash")
            return
        
        try:
            # Préparer les données pour Logstash
            logstash_data = {
                "@timestamp": datetime.now().isoformat(),
                "type": "dme_metrics",
                "metrics": data["data"],
                "collector": {
                    "version": "1.0",
                    "hostname": socket.gethostname()
                }
            }
            
            logger.debug(f"Connexion à Logstash: {self.config.LOGSTASH_HOST}:{self.config.LOGSTASH_PORT}")
            
            # Connexion TCP à Logstash
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            sock.connect((self.config.LOGSTASH_HOST, self.config.LOGSTASH_PORT))
            
            # Envoi des données en JSON Lines format
            message = json.dumps(logstash_data) + '\n'
            sock.sendall(message.encode('utf-8'))
            sock.close()
            
            logger.info(f"Données envoyées à Logstash: {len(logstash_data['metrics'])} métriques")
            logger.debug(f"Données Logstash: {logstash_data}")
            
        except socket.timeout:
            logger.error("Timeout lors de la connexion à Logstash")
        except ConnectionRefusedError:
            logger.error(f"Connexion refusée par Logstash ({self.config.LOGSTASH_HOST}:{self.config.LOGSTASH_PORT})")
        except Exception as e:
            logger.error(f"Erreur envoi Logstash: {str(e)}")
    
    def run_collection_cycle(self):
        """Exécute un cycle complet de collecte"""
        logger.info("=== DÉBUT CYCLE DE COLLECTE ===")
        
        # Collecte
        data = self.collect_data()
        if not data:
            logger.error("Échec de la collecte de données")
            return False
        
        # Formatage CSV
        formatted_data = self.format_data(data)
        if not formatted_data:
            logger.error("Échec du formatage des données")
            return False
        
        # Sauvegarde CSV
        csv_success = self.save_to_csv(formatted_data)
        
        # Envoi Logstash
        if self.config.LOGSTASH_ENABLED:
            self.send_to_logstash(data)
        else:
            logger.warning("Logstash désactivé - données non transmises à Elasticsearch")
        
        logger.info("=== FIN CYCLE DE COLLECTE ===")
        return csv_success
    
    def start_collection(self):
        """Démarre la collecte périodique"""
        logger.info(f"DÉMARRAGE COLLECTEUR DME (intervalle: {self.config.COLLECTION_INTERVAL}s)")
        
        while True:
            try:
                self.run_collection_cycle()
            except Exception as e:
                logger.error(f"Erreur cycle: {str(e)}")
            
            logger.info(f"Attente {self.config.COLLECTION_INTERVAL}s avant le prochain cycle...")
            time.sleep(self.config.COLLECTION_INTERVAL)

if __name__ == "__main__":
    try:
        collector = DMECollector()
        collector.start_collection()
    except KeyboardInterrupt:
        logger.info("Arrêt du collecteur (Ctrl+C)")
    except Exception as e:
        logger.critical(f"Erreur critique: {str(e)}")
        exit(1)
EOF
print_status "OK" "Collecteur mis à jour avec logs détaillés"

# 5. Créer un script de test post-déploiement
echo "5. Création du script de test..."
cat > test-complete-flow.sh << 'EOF'
#!/bin/bash
echo "=== TEST COMPLET DU FLUX DE DONNÉES ==="

echo "1. Attente du démarrage des services (60s)..."
sleep 60

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
EOF
chmod +x test-complete-flow.sh
print_status "OK" "Script de test créé"

# 6. Démarrage des services
echo "6. Démarrage des services avec la nouvelle configuration..."
docker-compose up -d

print_status "OK" "Services démarrés"

echo ""
echo "=== CONFIGURATION TERMINÉE ==="
echo ""
print_status "INFO" "INFORMATIONS DE CONNEXION:"
echo "  Elasticsearch:"
echo "    URL: http://localhost:9200"
echo "    Utilisateur: elastic"
echo "    Mot de passe: SuperAdmin123!"
echo ""
echo "  Kibana:"
echo "    URL: http://localhost:5601"
echo "    Utilisateur: elastic" 
echo "    Mot de passe: SuperAdmin123!"
echo ""
print_status "INFO" "PROCHAINES ÉTAPES:"
echo "  1. Attendre 2-3 minutes le démarrage complet"
echo "  2. Exécuter: ./test-complete-flow.sh"
echo "  3. Se connecter à Kibana avec elastic/SuperAdmin123!"
echo "  4. Créer un index pattern: rcms-dme-*"
echo ""
print_status "INFO" "Le collecteur envoie maintenant les données à Logstash toutes les 3 minutes"
print_status "INFO" "Les données apparaîtront dans Elasticsearch après le premier cycle"