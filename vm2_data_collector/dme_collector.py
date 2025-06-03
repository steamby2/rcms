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
