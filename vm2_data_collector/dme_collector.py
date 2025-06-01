#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Collecteur de données DME
Ce script collecte périodiquement les données du simulateur DME via des requêtes HTTP,
les formate et les enregistre dans un fichier CSV avec horodatage.

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
import ssl
import threading
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from requests.packages.urllib3.poolmanager import PoolManager

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
    # URL du simulateur DME (à modifier selon l'environnement)
    DME_SIMULATOR_URL = os.environ.get("DME_SIMULATOR_URL", "http://localhost:5000")
    
    # Intervalle de collecte en secondes (3 minutes par défaut)
    COLLECTION_INTERVAL = int(os.environ.get("COLLECTION_INTERVAL", 180))
    
    # Chemin du fichier de sortie
    OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "dme_data.csv")
    
    # Configuration pour Logstash (à activer en production)
    LOGSTASH_ENABLED = os.environ.get("LOGSTASH_ENABLED", "false").lower() == "true"
    LOGSTASH_HOST = os.environ.get("LOGSTASH_HOST", "localhost")
    LOGSTASH_PORT = int(os.environ.get("LOGSTASH_PORT", 5044))
    
    # Paramètres de sécurité
    VERIFY_SSL = os.environ.get("VERIFY_SSL", "true").lower() == "true"
    MAX_RETRIES = int(os.environ.get("MAX_RETRIES", 3))
    TIMEOUT = int(os.environ.get("TIMEOUT", 10))

# Classe pour gérer les connexions HTTPS avec vérification de certificat personnalisée
class SSLAdapter(HTTPAdapter):
    def __init__(self, *args, **kwargs):
        self.ssl_context = ssl.create_default_context()
        super().__init__(*args, **kwargs)
    
    def init_poolmanager(self, connections, maxsize, block=False):
        self.poolmanager = PoolManager(
            num_pools=connections,
            maxsize=maxsize,
            block=block,
            ssl_context=self.ssl_context
        )

# Classe pour collecter et traiter les données DME
class DMECollector:
    def __init__(self):
        self.config = Config()
        self.session = self._create_session()
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
    
    def _create_session(self):
        """Crée une session HTTP avec gestion des tentatives et des timeouts"""
        session = requests.Session()
        
        # Configuration des tentatives de reconnexion
        retry_strategy = Retry(
            total=self.config.MAX_RETRIES,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        
        # Utilisation de l'adaptateur SSL personnalisé si la vérification SSL est activée
        if self.config.VERIFY_SSL:
            adapter = SSLAdapter(max_retries=retry_strategy)
        else:
            adapter = HTTPAdapter(max_retries=retry_strategy)
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
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
        """Collecte les données du simulateur DME"""
        try:
            url = f"{self.config.DME_SIMULATOR_URL}/all"
            response = self.session.get(
                url,
                headers=self.headers,
                timeout=self.config.TIMEOUT,
                verify=self.config.VERIFY_SSL
            )
            
            if response.status_code == 200:
                data = response.json()
                logger.info("Données DME collectées avec succès")
                return data
            else:
                logger.error(f"Erreur lors de la collecte des données: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur de connexion au simulateur DME: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Erreur inattendue lors de la collecte des données: {str(e)}")
            return None
    
    def format_data(self, data):
        """Formate les données collectées pour l'enregistrement"""
        if not data or "data" not in data:
            return None
        
        dme_data = data["data"]
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-4]
        
        # Création d'une ligne de données formatée
        row = [timestamp]
        
        # Ajout des valeurs dans l'ordre des colonnes (en ignorant le timestamp)
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
        """Exécute un cycle complet de collecte, formatage et enregistrement"""
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
