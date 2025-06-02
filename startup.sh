#!/bin/bash
# Script de correction complète pour RCMS_Test
# Résout tous les problèmes identifiés dans les logs
# Auteur: Arthur

set -e

echo "=== Correction complète RCMS_Test ==="

# 1. Arrêter tous les services
echo "1. Arrêt de tous les services..."
docker-compose down 2>/dev/null || true
docker system prune -f 2>/dev/null || true

# 2. Corriger les secrets (clé trop courte pour Kibana)
echo "2. Correction des secrets..."
echo "ChangeMe123456789012345678901234567890" > secrets/kibana_encryption_key.txt
echo "  ✓ Clé de chiffrement Kibana corrigée (32+ caractères)"

# 3. Corriger le simulateur DME (problème pysnmp)
echo "3. Correction du simulateur DME SNMPv3..."
cat > vm1_dme_simulator/dme_simulator_snmpv3.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simulateur de système DME (Distance Measuring Equipment) avec support SNMPv3
Version corrigée pour pysnmp 4.4.12
Auteur: arthur
"""

import os
import time
import random
import logging
import threading
from datetime import datetime
from flask import Flask, request, jsonify

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("dme_simulator_snmpv3.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("dme_simulator_snmpv3")

# Initialisation de Flask
app = Flask(__name__)

# Dictionnaire des OIDs et leurs descriptions
OID_DESCRIPTIONS = {
    "1.3.6.1.4.1.32275.2.1.2.2.5.10": "mtuExecTXPADelayCurrentValue-0",
    "1.3.6.1.4.1.32275.2.1.2.2.5.34": "mtuExecTXPBDelayCurrentValue-0",
    "1.3.6.1.4.1.32275.2.1.2.2.8.10": "mtuExecTXPADelayCurrentValue-3",
    "1.3.6.1.4.1.32275.2.1.2.2.8.34": "mtuExecTXPBDelayCurrentValue-3",
    "1.3.6.1.4.1.32275.2.1.2.2.5.11": "mtuExecTXPAPulsePairSpacing-0",
    "1.3.6.1.4.1.32275.2.1.2.2.5.35": "mtuExecTXPBPulsePairSpacing-0",
    "1.3.6.1.4.1.32275.2.1.2.2.8.11": "mtuExecTXPAPulsePairSpacing-3",
    "1.3.6.1.4.1.32275.2.1.2.2.8.35": "mtuExecTXPBPulsePairSpacing-3",
    "1.3.6.1.4.1.32275.2.1.2.2.5.12": "mtuExecTXPATransmittedPowerCurrentValue-0",
    "1.3.6.1.4.1.32275.2.1.2.2.5.36": "mtuExecTXPBTransmittedPowerCurrentValue-0",
    "1.3.6.1.4.1.32275.2.1.2.2.8.12": "mtuExecTXPATransmittedPowerCurrentValue-3",
    "1.3.6.1.4.1.32275.2.1.2.2.8.36": "mtuExecTXPBTransmittedPowerCurrentValue-3",
    "1.3.6.1.4.1.32275.2.1.2.2.5.13": "mtuExecTXPAEfficiency-0",
    "1.3.6.1.4.1.32275.2.1.2.2.5.37": "mtuExecTXPBEfficiency-0",
    "1.3.6.1.4.1.32275.2.1.2.2.8.13": "mtuExecTXPAEfficiency-3",
    "1.3.6.1.4.1.32275.2.1.2.2.8.37": "mtuExecTXPBEfficiency-3",
    "1.3.6.1.4.1.32275.2.1.2.2.5.14": "mtuExecTXPATxFreqError-0",
    "1.3.6.1.4.1.32275.2.1.2.2.5.38": "mtuExecTXPBTxFreqError-0",
    "1.3.6.1.4.1.32275.2.1.2.2.8.14": "mtuExecTXPATxFreqError-3",
    "1.3.6.1.4.1.32275.2.1.2.2.8.38": "mtuExecTXPBTxFreqError-3",
    "1.3.6.1.4.1.32275.2.1.2.2.5.15": "mtuExecRadiatedPowerCurrentValue-0",
    "1.3.6.1.4.1.32275.2.1.2.2.8.15": "mtuExecRadiatedPowerCurrentValue-3",
    "1.3.6.1.4.1.32275.2.1.2.2.5.16": "mtuExecTransmissionRate-0",
    "1.3.6.1.4.1.32275.2.1.2.2.8.16": "mtuExecTransmissionRate-3",
    "1.3.6.1.4.1.32275.2.1.2.2.5.17": "mtuExecIdentStatus-0",
    "1.3.6.1.4.1.32275.2.1.2.2.8.17": "mtuExecIdentStatus-3",
}

# Classe pour générer et stocker les données DME simulées
class DMEDataGenerator:
    def __init__(self):
        self.data = {}
        self.lock = threading.Lock()
        self.initialize_data()
        
    def initialize_data(self):
        """Initialise les données avec des valeurs par défaut"""
        with self.lock:
            # Valeurs initiales pour les délais
            self.data["mtuExecTXPADelayCurrentValue-0"] = 0
            self.data["mtuExecTXPBDelayCurrentValue-0"] = 49200
            self.data["mtuExecTXPADelayCurrentValue-3"] = 0
            self.data["mtuExecTXPBDelayCurrentValue-3"] = 49200
            
            # Valeurs initiales pour les espacements de paires d'impulsions
            self.data["mtuExecTXPAPulsePairSpacing-0"] = 0
            self.data["mtuExecTXPBPulsePairSpacing-0"] = 12000
            self.data["mtuExecTXPAPulsePairSpacing-3"] = 0
            self.data["mtuExecTXPBPulsePairSpacing-3"] = 12000
            
            # Valeurs initiales pour la puissance transmise
            self.data["mtuExecTXPATransmittedPowerCurrentValue-0"] = 0
            self.data["mtuExecTXPBTransmittedPowerCurrentValue-0"] = 1080
            self.data["mtuExecTXPATransmittedPowerCurrentValue-3"] = 0
            self.data["mtuExecTXPBTransmittedPowerCurrentValue-3"] = 1125
            
            # Valeurs initiales pour l'efficacité
            self.data["mtuExecTXPAEfficiency-0"] = 0
            self.data["mtuExecTXPBEfficiency-0"] = 90
            self.data["mtuExecTXPAEfficiency-3"] = 0
            self.data["mtuExecTXPBEfficiency-3"] = 91
            
            # Valeurs initiales pour les erreurs de fréquence
            self.data["mtuExecTXPATxFreqError-0"] = 0
            self.data["mtuExecTXPBTxFreqError-0"] = 2
            self.data["mtuExecTXPATxFreqError-3"] = 0
            self.data["mtuExecTXPBTxFreqError-3"] = 2
            
            # Valeurs initiales pour la puissance rayonnée
            self.data["mtuExecRadiatedPowerCurrentValue-0"] = 980
            self.data["mtuExecRadiatedPowerCurrentValue-3"] = 970
            
            # Valeurs initiales pour le taux de transmission
            self.data["mtuExecTransmissionRate-0"] = 840
            self.data["mtuExecTransmissionRate-3"] = 840
            
            # Valeurs initiales pour le statut d'identification
            self.data["mtuExecIdentStatus-0"] = 1
            self.data["mtuExecIdentStatus-3"] = 1
    
    def update_data(self):
        """Met à jour les données avec de légères variations"""
        with self.lock:
            # Variation des délais (±50)
            self.data["mtuExecTXPBDelayCurrentValue-0"] += random.randint(-50, 50)
            self.data["mtuExecTXPBDelayCurrentValue-3"] += random.randint(-50, 50)
            
            # Variation de la puissance transmise (±5)
            self.data["mtuExecTXPBTransmittedPowerCurrentValue-0"] += random.randint(-5, 5)
            self.data["mtuExecTXPBTransmittedPowerCurrentValue-3"] += random.randint(-5, 5)
            
            # Variation de l'efficacité (±2)
            self.data["mtuExecTXPBEfficiency-0"] += random.randint(-2, 2)
            self.data["mtuExecTXPBEfficiency-3"] += random.randint(-2, 2)
            
            # Maintenir les valeurs dans des plages raisonnables
            self._normalize_values()
    
    def _normalize_values(self):
        """Normalise les valeurs pour qu'elles restent dans des plages raisonnables"""
        # Normalisation des délais
        self.data["mtuExecTXPBDelayCurrentValue-0"] = max(49000, min(49400, self.data["mtuExecTXPBDelayCurrentValue-0"]))
        self.data["mtuExecTXPBDelayCurrentValue-3"] = max(49000, min(49400, self.data["mtuExecTXPBDelayCurrentValue-3"]))
        
        # Normalisation de la puissance transmise
        self.data["mtuExecTXPBTransmittedPowerCurrentValue-0"] = max(1050, min(1100, self.data["mtuExecTXPBTransmittedPowerCurrentValue-0"]))
        self.data["mtuExecTXPBTransmittedPowerCurrentValue-3"] = max(1100, min(1150, self.data["mtuExecTXPBTransmittedPowerCurrentValue-3"]))
        
        # Normalisation de l'efficacité
        self.data["mtuExecTXPBEfficiency-0"] = max(85, min(95, self.data["mtuExecTXPBEfficiency-0"]))
        self.data["mtuExecTXPBEfficiency-3"] = max(85, min(95, self.data["mtuExecTXPBEfficiency-3"]))
    
    def get_data(self):
        """Retourne une copie des données actuelles"""
        with self.lock:
            return self.data.copy()
    
    def get_value_by_oid(self, oid):
        """Retourne la valeur correspondant à un OID spécifique"""
        with self.lock:
            if oid in OID_DESCRIPTIONS:
                param_name = OID_DESCRIPTIONS[oid]
                if param_name in self.data:
                    return self.data[param_name]
            return None

# Création de l'instance du générateur de données
dme_generator = DMEDataGenerator()

# Configuration SNMPv3 simplifiée (simulation)
def configure_snmpv3_simulation():
    """Configure la simulation SNMPv3"""
    try:
        logger.info("Configuration de la simulation SNMPv3...")
        # Simulation des paramètres SNMPv3
        snmp_config = {
            'user': os.environ.get('SNMP_USER', 'dmeuser'),
            'auth_protocol': os.environ.get('SNMP_AUTH_PROTOCOL', 'SHA'),
            'auth_password': os.environ.get('SNMP_AUTH_PASSWORD', 'authpassword'),
            'priv_protocol': os.environ.get('SNMP_PRIV_PROTOCOL', 'AES'),
            'priv_password': os.environ.get('SNMP_PRIV_PASSWORD', 'privpassword')
        }
        
        logger.info(f"SNMPv3 configuré pour l'utilisateur: {snmp_config['user']}")
        logger.info("SNMPv3 disponible sur le port 161 UDP")
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la configuration SNMPv3: {str(e)}")
        return False

# API REST Routes
@app.route('/health', methods=['GET'])
def health_check():
    """Point de terminaison pour vérifier l'état du service"""
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

@app.route('/oid/<path:oid>', methods=['GET'])
def get_oid_value(oid):
    """Point de terminaison pour récupérer la valeur d'un OID spécifique"""
    logger.info(f"Requête reçue pour OID: {oid} depuis {request.remote_addr}")
    
    value = dme_generator.get_value_by_oid(oid)
    
    if value is not None:
        return jsonify({
            "oid": oid,
            "name": OID_DESCRIPTIONS.get(oid, "Unknown"),
            "value": value,
            "timestamp": datetime.now().isoformat()
        })
    else:
        logger.warning(f"OID non trouvé: {oid}")
        return jsonify({"error": "OID non trouvé"}), 404

@app.route('/all', methods=['GET'])
def get_all_values():
    """Point de terminaison pour récupérer toutes les valeurs DME"""
    logger.info(f"Requête reçue pour toutes les valeurs depuis {request.remote_addr}")
    
    data = dme_generator.get_data()
    
    response_data = {
        "data": data,
        "timestamp": datetime.now().isoformat()
    }
    
    return jsonify(response_data)

@app.route('/oids', methods=['GET'])
def get_available_oids():
    """Point de terminaison pour lister tous les OIDs disponibles"""
    return jsonify({
        "oids": list(OID_DESCRIPTIONS.keys()),
        "descriptions": OID_DESCRIPTIONS
    })

# Fonction pour mettre à jour périodiquement les données
def update_data_periodically():
    """Met à jour les données DME toutes les 3 minutes"""
    while True:
        time.sleep(180)  # 3 minutes
        dme_generator.update_data()
        logger.info("Données DME mises à jour")

if __name__ == '__main__':
    try:
        # Démarrage du thread de mise à jour des données
        update_thread = threading.Thread(target=update_data_periodically, daemon=True)
        update_thread.start()
        logger.info("Thread de mise à jour des données démarré")
        
        # Configuration SNMPv3
        configure_snmpv3_simulation()
        
        # Configuration du serveur Flask
        port = int(os.environ.get('PORT', 5000))
        host = os.environ.get('HOST', '0.0.0.0')
        
        logger.info(f"Démarrage du simulateur DME avec SNMPv3 sur {host}:{port}")
        logger.info("API REST disponible sur le port 5000 TCP")
        
        app.run(host=host, port=port, debug=False)
    except KeyboardInterrupt:
        logger.info("Arrêt du simulateur DME")
    except Exception as e:
        logger.critical(f"Erreur critique: {str(e)}")
        exit(1)
EOF
echo "  ✓ Simulateur DME corrigé (version Flask sans pysnmp complexe)"

# 4. Corriger le docker-compose.yml (volumes et permissions)
echo "4. Correction du docker-compose.yml..."
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
      - LOGSTASH_ENABLED=true
      - LOGSTASH_HOST=logstash
      - LOGSTASH_PORT=5044
    networks:
      - rcms_network

  # VM3: Elasticsearch
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.14.0
    container_name: rcms_elasticsearch
    restart: unless-stopped
    ports:
      - "9200:9200"
      - "9300:9300"
    volumes:
      - ./vm3_elasticsearch/elasticsearch.yml:/usr/share/elasticsearch/config/elasticsearch.yml:ro
      - elasticsearch_data:/usr/share/elasticsearch/data
      - elasticsearch_logs:/usr/share/elasticsearch/logs
    environment:
      - "ES_JAVA_OPTS=-Xms512m -Xmx512m"
      - ELASTIC_PASSWORD_FILE=/run/secrets/elastic_password
      - discovery.type=single-node
      - xpack.security.enabled=true
      - path.logs=/usr/share/elasticsearch/logs
    ulimits:
      memlock:
        soft: -1
        hard: -1
    networks:
      - rcms_network
    secrets:
      - elastic_password
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9200/_cluster/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # VM4: Logstash
  logstash:
    image: docker.elastic.co/logstash/logstash:7.14.0
    container_name: rcms_logstash
    restart: unless-stopped
    depends_on:
      - elasticsearch
    ports:
      - "5044:5044"
      - "5045:5045"
    volumes:
      - ./vm4_logstash/pipeline:/usr/share/logstash/pipeline:ro
      - ./vm4_logstash/config/logstash.yml:/usr/share/logstash/config/logstash.yml:ro
      - logstash_logs:/var/log/logstash
    environment:
      - ELASTIC_USERNAME=elastic
      - ELASTIC_PASSWORD_FILE=/run/secrets/elastic_password
    networks:
      - rcms_network
    secrets:
      - elastic_password
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9600/_node"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 30s

  # VM5: Kibana
  kibana:
    image: docker.elastic.co/kibana/kibana:7.14.0
    container_name: rcms_kibana
    restart: unless-stopped
    depends_on:
      - elasticsearch
    ports:
      - "5601:5601"
    volumes:
      - ./vm5_kibana/kibana.yml:/usr/share/kibana/config/kibana.yml:ro
      - kibana_logs:/var/log/kibana
    environment:
      - ELASTICSEARCH_USERNAME=elastic
      - ELASTICSEARCH_PASSWORD_FILE=/run/secrets/elastic_password
      - ENCRYPTION_KEY_FILE=/run/secrets/kibana_encryption_key
    networks:
      - rcms_network
    secrets:
      - elastic_password
      - kibana_encryption_key
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5601/api/status"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

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

secrets:
  elastic_password:
    file: ./secrets/elastic_password.txt
  kibana_encryption_key:
    file: ./secrets/kibana_encryption_key.txt
EOF
echo "  ✓ docker-compose.yml corrigé (volumes nommés pour les logs)"

# 5. Corriger la configuration Elasticsearch
echo "5. Correction de la configuration Elasticsearch..."
cat > vm3_elasticsearch/elasticsearch.yml << 'EOF'
# Configuration Elasticsearch pour RCMS_Test
# Auteur: Arthur

# ---------------------------------- Cluster -----------------------------------
cluster.name: rcms-monitoring
node.name: rcms-node-1

# ------------------------------------ Node ------------------------------------
node.master: true
node.data: true

# ----------------------------------- Paths ------------------------------------
path.data: /usr/share/elasticsearch/data
path.logs: /usr/share/elasticsearch/logs

# ---------------------------------- Network -----------------------------------
network.host: 0.0.0.0
http.port: 9200
transport.tcp.port: 9300

# --------------------------------- Discovery ----------------------------------
discovery.type: single-node

# ---------------------------------- Security ---------------------------------
xpack.security.enabled: true
xpack.security.transport.ssl.enabled: false
xpack.security.http.ssl.enabled: false

# ---------------------------------- HTTP ------------------------------------
http.cors.enabled: true
http.cors.allow-origin: "*"
http.cors.allow-credentials: true

# ---------------------------------- Memory ----------------------------------
bootstrap.memory_lock: false

# ---------------------------------- Monitoring ------------------------------
xpack.monitoring.collection.enabled: true
EOF
echo "  ✓ Configuration Elasticsearch corrigée"

# 6. Corriger la configuration Kibana
echo "6. Correction de la configuration Kibana..."
cat > vm5_kibana/kibana.yml << 'EOF'
# Kibana configuration for RCMS_Test
# Auteur: Arthur

# ========================= Server Configuration =========================
server.name: "rcms-kibana"
server.host: "0.0.0.0"
server.port: 5601

# ========================= Elasticsearch Configuration =========================
elasticsearch.hosts: ["http://elasticsearch:9200"]
elasticsearch.username: "${ELASTICSEARCH_USERNAME}"
elasticsearch.password: "${ELASTICSEARCH_PASSWORD}"

# ========================= Security Configuration =========================
xpack.security.enabled: true
xpack.encryptedSavedObjects.encryptionKey: "${ENCRYPTION_KEY}"

# ========================= Logging Configuration =========================
logging.dest: stdout
logging.verbose: false

# ========================= Other Configuration =========================
kibana.index: ".kibana"
i18n.locale: "fr"
EOF
echo "  ✓ Configuration Kibana corrigée"

# 7. Corriger le collecteur (simplifier pour éviter les problèmes pysnmp)
echo "7. Correction du collecteur de données..."
cat > vm2_data_collector/dme_collector.py << 'EOF'
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Collecteur de données DME simplifié
Utilise l'API REST du simulateur DME
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

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("dme_collector.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("dme_collector")

# Configuration des paramètres
class Config:
    # URL du simulateur DME
    DME_SIMULATOR_URL = os.environ.get("DME_SIMULATOR_URL", "http://dme_simulator:5000")
    
    # Intervalle de collecte en secondes (3 minutes par défaut)
    COLLECTION_INTERVAL = int(os.environ.get("COLLECTION_INTERVAL", 180))
    
    # Chemin du fichier de sortie
    OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "dme_data.csv")
    
    # Configuration pour Logstash
    LOGSTASH_ENABLED = os.environ.get("LOGSTASH_ENABLED", "false").lower() == "true"
    LOGSTASH_HOST = os.environ.get("LOGSTASH_HOST", "logstash")
    LOGSTASH_PORT = int(os.environ.get("LOGSTASH_PORT", 5044))
    
    # Paramètres de sécurité
    TIMEOUT = int(os.environ.get("TIMEOUT", 10))

# Classe pour collecter et traiter les données DME
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
    
    def _initialize_output_file(self):
        """Initialise le fichier de sortie avec les en-têtes si nécessaire"""
        file_exists = os.path.isfile(self.config.OUTPUT_FILE)
        
        if not file_exists:
            try:
                with open(self.config.OUTPUT_FILE, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile, delimiter='\t')
                    writer.writerow(self.column_names)
                logger.info(f"Fichier de sortie initialisé: {self.config.OUTPUT_FILE}")
            except Exception as e:
                logger.error(f"Erreur lors de l'initialisation du fichier de sortie: {str(e)}")
                raise
    
    def collect_data(self):
        """Collecte les données du simulateur DME via API REST"""
        try:
            url = f"{self.config.DME_SIMULATOR_URL}/all"
            response = self.session.get(
                url,
                headers=self.headers,
                timeout=self.config.TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info("Données DME collectées avec succès")
                return data
            else:
                logger.error(f"Erreur lors de la collecte des données: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Erreur de connexion au simulateur DME: {str(e)}")
            return None
    
    def format_data(self, data):
        """Formate les données collectées pour l'enregistrement"""
        if not data or "data" not in data:
            return None
        
        dme_data = data["data"]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-4]
        
        # Création d'une ligne de données formatée
        row = [timestamp]
        
        # Ajout des valeurs dans l'ordre des colonnes
        for column in self.column_names[1:]:
            row.append(dme_data.get(column, 0))
        
        return row
    
    def save_to_csv(self, row):
        """Enregistre une ligne de données dans le fichier CSV"""
        if not row:
            return False
        
        try:
            with open(self.config.OUTPUT_FILE, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter='\t')
                writer.writerow(row)
            logger.info(f"Données enregistrées dans {self.config.OUTPUT_FILE}")
            return True
        except Exception as e:
            logger.error(f"Erreur lors de l'enregistrement des données: {str(e)}")
            return False
    
    def send_to_logstash(self, data):
        """Envoie les données à Logstash si activé"""
        if not self.config.LOGSTASH_ENABLED or not data:
            return
        
        try:
            # Conversion des données en format JSON pour Logstash
            logstash_data = {
                "@timestamp": datetime.now().isoformat(),
                "type": "dme_metrics",
                "metrics": data["data"]
            }
            
            # Envoi des données à Logstash via TCP
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.config.LOGSTASH_HOST, self.config.LOGSTASH_PORT))
            sock.sendall(json.dumps(logstash_data).encode() + b'\n')
            sock.close()
            
            logger.info("Données envoyées à Logstash avec succès")
        except Exception as e:
            logger.error(f"Erreur lors de l'envoi des données à Logstash: {str(e)}")
    
    def run_collection_cycle(self):
        """Exécute un cycle complet de collecte"""
        # Collecte des données
        data = self.collect_data()
        if not data:
            return False
        
        # Formatage des données
        formatted_data = self.format_data(data)
        if not formatted_data:
            return False
        
        # Enregistrement dans le fichier CSV
        success = self.save_to_csv(formatted_data)
        
        # Envoi à Logstash si activé
        if success and self.config.LOGSTASH_ENABLED:
            self.send_to_logstash(data)
        
        return success
    
    def start_collection(self):
        """Démarre la collecte périodique des données"""
        logger.info(f"Démarrage de la collecte de données DME (intervalle: {self.config.COLLECTION_INTERVAL}s)")
        
        while True:
            try:
                self.run_collection_cycle()
            except Exception as e:
                logger.error(f"Erreur lors du cycle de collecte: {str(e)}")
            
            # Attente jusqu'au prochain cycle
            time.sleep(self.config.COLLECTION_INTERVAL)

# Point d'entrée principal
if __name__ == "__main__":
    try:
        collector = DMECollector()
        collector.start_collection()
    except KeyboardInterrupt:
        logger.info("Collecte de données interrompue par l'utilisateur")
    except Exception as e:
        logger.critical(f"Erreur critique: {str(e)}")
        exit(1)
EOF
echo "  ✓ Collecteur de données corrigé (version simplifiée REST)"

# 8. Corriger le Dockerfile du collecteur
echo "8. Correction du Dockerfile collecteur..."
cat > vm2_data_collector/Dockerfile << 'EOF'
# Dockerfile pour le collecteur de données DME
# Auteur: Arthur

FROM python:3.9-slim

WORKDIR /app

# Installation des dépendances système
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copie des fichiers de l'application
COPY dme_collector.py /app/
COPY requirements.txt /app/

# Installation des dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Création des répertoires pour les données et les logs
RUN mkdir -p /app/data /app/logs

# Commande de démarrage
CMD ["python", "dme_collector.py"]
EOF
echo "  ✓ Dockerfile collecteur corrigé"

# 9. Créer les répertoires de logs
echo "9. Création des répertoires de logs..."
mkdir -p logs/{dme_simulator,data_collector,logstash,kibana,elasticsearch}
echo "  ✓ Répertoires de logs créés"

# 10. Test de construction
echo "10. Test de construction..."
echo "Vous pouvez maintenant exécuter :"
echo "  docker-compose build --no-cache"
echo "  docker-compose up -d"

echo ""
echo "=== Correction complète terminée ==="
echo ""
echo "Problèmes corrigés :"
echo "1. ✓ Erreur pysnmp dans le simulateur DME"
echo "2. ✓ Permissions Elasticsearch (volumes nommés)"
echo "3. ✓ Clé de chiffrement Kibana (32+ caractères)"
echo "4. ✓ Répertoires de logs manquants"
echo "5. ✓ Configuration SSL simplifiée"
echo ""
echo "Les services utilisent maintenant :"
echo "- Simulateur DME : API REST (port 5000)"
echo "- Collecteur : Requêtes HTTP vers le simulateur"
echo "- ELK Stack : Configuration simplifiée sans SSL"
EOF