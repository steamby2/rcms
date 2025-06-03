#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Collecteur DME simplifié - Version 100% fonctionnelle
Génère les données DME et les envoie à Logstash/CSV
Auteur: arthur
"""

import os
import time
import csv
import json
import logging
import random
import socket
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/app/logs/snmp_collector.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("snmp_collector")

# Configuration
class Config:
    COLLECTION_INTERVAL = int(os.environ.get("COLLECTION_INTERVAL", 10))
    OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "/app/data/dme_data.csv")
    
    LOGSTASH_ENABLED = os.environ.get("LOGSTASH_ENABLED", "true").lower() == "true"
    LOGSTASH_HOST = os.environ.get("LOGSTASH_HOST", "logstash")
    LOGSTASH_PORT = int(os.environ.get("LOGSTASH_PORT", 5044))

# OIDs et noms
DME_OIDS = {
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

class SimpleCollector:
    def __init__(self):
        self.config = Config()
        self.column_names = ["Timestamp"] + list(DME_OIDS.values())
        self._initialize_output_file()
        
        # État initial des données
        self.dme_data = {
            "mtuExecTXPADelayCurrentValue-0": 0,
            "mtuExecTXPBDelayCurrentValue-0": 49200,
            "mtuExecTXPADelayCurrentValue-3": 0,
            "mtuExecTXPBDelayCurrentValue-3": 49200,
            "mtuExecTXPAPulsePairSpacing-0": 0,
            "mtuExecTXPBPulsePairSpacing-0": 12000,
            "mtuExecTXPAPulsePairSpacing-3": 0,
            "mtuExecTXPBPulsePairSpacing-3": 12000,
            "mtuExecTXPATransmittedPowerCurrentValue-0": 0,
            "mtuExecTXPBTransmittedPowerCurrentValue-0": 1080,
            "mtuExecTXPATransmittedPowerCurrentValue-3": 0,
            "mtuExecTXPBTransmittedPowerCurrentValue-3": 1125,
            "mtuExecTXPAEfficiency-0": 0,
            "mtuExecTXPBEfficiency-0": 90,
            "mtuExecTXPAEfficiency-3": 0,
            "mtuExecTXPBEfficiency-3": 91,
            "mtuExecTXPATxFreqError-0": 0,
            "mtuExecTXPBTxFreqError-0": 2,
            "mtuExecTXPATxFreqError-3": 0,
            "mtuExecTXPBTxFreqError-3": 2,
            "mtuExecRadiatedPowerCurrentValue-0": 980,
            "mtuExecRadiatedPowerCurrentValue-3": 970,
            "mtuExecTransmissionRate-0": 840,
            "mtuExecTransmissionRate-3": 840,
            "mtuExecIdentStatus-0": 1,
            "mtuExecIdentStatus-3": 1,
        }
        
        logger.info("Collecteur DME simplifié initialisé")
        logger.info(f"Intervalle: {self.config.COLLECTION_INTERVAL}s")
        logger.info(f"Logstash: {self.config.LOGSTASH_ENABLED}")
        logger.info(f"OIDs: {len(DME_OIDS)}")
    
    def _initialize_output_file(self):
        """Initialise le fichier CSV"""
        if not os.path.isfile(self.config.OUTPUT_FILE):
            try:
                os.makedirs(os.path.dirname(self.config.OUTPUT_FILE), exist_ok=True)
                with open(self.config.OUTPUT_FILE, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile, delimiter='\t')
                    writer.writerow(self.column_names)
                logger.info(f"Fichier CSV initialisé: {self.config.OUTPUT_FILE}")
            except Exception as e:
                logger.error(f"Erreur init CSV: {str(e)}")
                raise
    
    def update_values(self):
        """Met à jour les valeurs avec des variations réalistes"""
        # Variation des délais
        self.dme_data["mtuExecTXPBDelayCurrentValue-0"] += random.randint(-50, 50)
        self.dme_data["mtuExecTXPBDelayCurrentValue-3"] += random.randint(-50, 50)
        
        # Variation de la puissance
        self.dme_data["mtuExecTXPBTransmittedPowerCurrentValue-0"] += random.randint(-5, 5)
        self.dme_data["mtuExecTXPBTransmittedPowerCurrentValue-3"] += random.randint(-5, 5)
        
        # Variation de l'efficacité
        self.dme_data["mtuExecTXPBEfficiency-0"] += random.randint(-2, 2)
        self.dme_data["mtuExecTXPBEfficiency-3"] += random.randint(-2, 2)
        
        # Normaliser
        self.dme_data["mtuExecTXPBDelayCurrentValue-0"] = max(49000, min(49400, self.dme_data["mtuExecTXPBDelayCurrentValue-0"]))
        self.dme_data["mtuExecTXPBDelayCurrentValue-3"] = max(49000, min(49400, self.dme_data["mtuExecTXPBDelayCurrentValue-3"]))
        
        self.dme_data["mtuExecTXPBTransmittedPowerCurrentValue-0"] = max(1050, min(1100, self.dme_data["mtuExecTXPBTransmittedPowerCurrentValue-0"]))
        self.dme_data["mtuExecTXPBTransmittedPowerCurrentValue-3"] = max(1100, min(1150, self.dme_data["mtuExecTXPBTransmittedPowerCurrentValue-3"]))
        
        self.dme_data["mtuExecTXPBEfficiency-0"] = max(85, min(95, self.dme_data["mtuExecTXPBEfficiency-0"]))
        self.dme_data["mtuExecTXPBEfficiency-3"] = max(85, min(95, self.dme_data["mtuExecTXPBEfficiency-3"]))
    
    def collect_data(self):
        """Collecte les données DME"""
        logger.info("=== COLLECTE DME ===")
        
        # Mettre à jour les valeurs
        self.update_values()
        
        logger.info(f"✓ Collecte réussie: {len(self.dme_data)} métriques")
        return self.dme_data
    
    def format_data(self, data):
        """Formate les données pour CSV"""
        if not data:
            return None
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-4]
        row = [timestamp]
        
        for column in self.column_names[1:]:
            row.append(data.get(column, 0))
        
        return row
    
    def save_to_csv(self, row):
        """Sauvegarde CSV"""
        if not row:
            return False
        
        try:
            with open(self.config.OUTPUT_FILE, 'a', newline='') as csvfile:
                writer = csv.writer(csvfile, delimiter='\t')
                writer.writerow(row)
            logger.info("✓ Données CSV sauvegardées")
            return True
        except Exception as e:
            logger.error(f"Erreur CSV: {str(e)}")
            return False
    
    def send_to_logstash(self, data):
        """Envoi vers Logstash"""
        if not self.config.LOGSTASH_ENABLED or not data:
            return
        
        try:
            logstash_data = {
                "@timestamp": datetime.now().isoformat(),
                "type": "dme_metrics",
                "metrics": data,
                "collection_method": "dme_simulation",
                "collector": {
                    "version": "4.0",
                    "mode": "simulation",
                    "interval": self.config.COLLECTION_INTERVAL
                }
            }
            
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            sock.connect((self.config.LOGSTASH_HOST, self.config.LOGSTASH_PORT))
            
            message = json.dumps(logstash_data) + '\n'
            sock.sendall(message.encode('utf-8'))
            sock.close()
            
            logger.info("✓ Données envoyées à Logstash")
            
        except Exception as e:
            logger.error(f"Erreur Logstash: {str(e)}")
    
    def run_collection_cycle(self):
        """Cycle complet de collecte"""
        data = self.collect_data()
        if not data:
            return False
        
        formatted_data = self.format_data(data)
        if not formatted_data:
            return False
        
        success = self.save_to_csv(formatted_data)
        
        if success and self.config.LOGSTASH_ENABLED:
            self.send_to_logstash(data)
        
        logger.info("=== FIN CYCLE ===")
        return success
    
    def start_collection(self):
        """Démarre la collecte périodique"""
        logger.info("DÉMARRAGE COLLECTEUR DME SIMPLIFIÉ")
        logger.info("Mode: Simulation complète avec données réalistes")
        
        while True:
            try:
                self.run_collection_cycle()
            except Exception as e:
                logger.error(f"Erreur cycle: {str(e)}")
            
            logger.info(f"Attente {self.config.COLLECTION_INTERVAL}s...")
            time.sleep(self.config.COLLECTION_INTERVAL)

if __name__ == "__main__":
    try:
        collector = SimpleCollector()
        collector.start_collection()
    except KeyboardInterrupt:
        logger.info("Arrêt collecteur (Ctrl+C)")
    except Exception as e:
        logger.critical(f"Erreur critique: {str(e)}")
        exit(1)
