#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Collecteur de données DME avec support SNMPv3
Ce script collecte périodiquement les données du simulateur DME via des requêtes SNMPv3,
les formate et les enregistre dans un fichier CSV avec horodatage.

Auteur: arthur

"""

import os
import time
import csv
import json
import logging
import subprocess
import threading
from datetime import datetime
import socket
import ssl
from pysnmp.hlapi import (
    SnmpEngine,
    UdpTransportTarget,
    ContextData,
    ObjectType,
    ObjectIdentity,
    getCmd,
    UsmUserData,
    usmHMACSHAAuthProtocol,
    usmHMACMD5AuthProtocol,
    usmAesCfb128Protocol,
    usmDESPrivProtocol,
)

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("dme_collector_snmpv3.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("dme_collector_snmpv3")

# Configuration des paramètres
class Config:
    # Paramètres SNMPv3
    SNMP_HOST = os.environ.get("SNMP_HOST", "dme_simulator_snmpv3")
    SNMP_PORT = int(os.environ.get("SNMP_PORT", 161))
    SNMP_USER = os.environ.get("SNMP_USER", "dmeuser")
    SNMP_AUTH_PROTOCOL = os.environ.get("SNMP_AUTH_PROTOCOL", "SHA")
    SNMP_AUTH_PASSWORD = os.environ.get("SNMP_AUTH_PASSWORD", "authpassword")
    SNMP_PRIV_PROTOCOL = os.environ.get("SNMP_PRIV_PROTOCOL", "AES")
    SNMP_PRIV_PASSWORD = os.environ.get("SNMP_PRIV_PASSWORD", "privpassword")
    
    # Intervalle de collecte en secondes (3 minutes par défaut)
    COLLECTION_INTERVAL = int(os.environ.get("COLLECTION_INTERVAL", 180))
    
    # Chemin du fichier de sortie
    OUTPUT_FILE = os.environ.get("OUTPUT_FILE", "dme_data.csv")
    
    # Configuration pour Logstash (à activer en production)
    LOGSTASH_ENABLED = os.environ.get("LOGSTASH_ENABLED", "false").lower() == "true"
    LOGSTASH_HOST = os.environ.get("LOGSTASH_HOST", "logstash")
    LOGSTASH_PORT = int(os.environ.get("LOGSTASH_PORT", 5044))
    
    # Paramètres de sécurité
    MAX_RETRIES = int(os.environ.get("MAX_RETRIES", 3))
    TIMEOUT = int(os.environ.get("TIMEOUT", 10))

# Liste des OIDs à collecter
OID_LIST = {
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

# Classe pour collecter et traiter les données DME
class DMECollector:
    def __init__(self):
        self.config = Config()
        self.column_names = ["Timestamp"] + list(OID_LIST.values())
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
    
    def collect_data_snmpv3(self):
        """Collecte les données du simulateur DME via SNMPv3"""
        data = {}
        
        try:
            if self.config.SNMP_AUTH_PROTOCOL.upper() == "SHA":
                auth_protocol = usmHMACSHAAuthProtocol
            else:
                auth_protocol = usmHMACMD5AuthProtocol

            if self.config.SNMP_PRIV_PROTOCOL.upper() == "AES":
                priv_protocol = usmAesCfb128Protocol
            else:
                priv_protocol = usmDESPrivProtocol

            auth_data = UsmUserData(
                self.config.SNMP_USER,
                self.config.SNMP_AUTH_PASSWORD,
                self.config.SNMP_PRIV_PASSWORD,
                authProtocol=auth_protocol,
                privProtocol=priv_protocol,
            )

            for oid, name in OID_LIST.items():
                iterator = getCmd(
                    SnmpEngine(),
                    auth_data,
                    UdpTransportTarget(
                        (self.config.SNMP_HOST, self.config.SNMP_PORT),
                        timeout=self.config.TIMEOUT,
                        retries=self.config.MAX_RETRIES,
                    ),
                    ContextData(),
                    ObjectType(ObjectIdentity(oid)),
                )

                error_indication, error_status, error_index, var_binds = next(iterator)

                if error_indication:
                    logger.error(f"Erreur SNMP: {error_indication}")
                    continue
                elif error_status:
                    logger.error(
                        f"Erreur SNMP: {error_status.prettyPrint()} à l'index {error_index}"
                    )
                    continue

                for var_bind in var_binds:
                    value = var_bind[1]
                    data[name] = int(value)
                    logger.debug(f"Collecté {name}: {value}")
            
            logger.info("Données DME collectées avec succès via SNMPv3")
            return data
        except Exception as e:
            logger.error(f"Erreur lors de la collecte des données via SNMPv3: {str(e)}")
            return None
    
    def collect_data_curl(self):
        """Collecte les données du simulateur DME via curl (méthode alternative)"""
        try:
            # Construction de la commande curl avec authentification SNMPv3
            curl_command = [
                "curl", "-s",
                "-u", f"{self.config.SNMP_USER}:{self.config.SNMP_AUTH_PASSWORD}",
                f"http://{self.config.SNMP_HOST}:5000/all"
            ]
            
            # Exécution de la commande curl
            process = subprocess.Popen(curl_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            stdout, stderr = process.communicate()
            
            # Vérification des erreurs
            if process.returncode != 0:
                logger.error(f"Erreur curl: {stderr.decode('utf-8')}")
                return None
            
            # Analyse de la réponse JSON
            response = json.loads(stdout.decode('utf-8'))
            
            if "data" in response:
                logger.info("Données DME collectées avec succès via curl")
                return response["data"]
            else:
                logger.error("Format de réponse curl invalide")
                return None
        except Exception as e:
            logger.error(f"Erreur lors de la collecte des données via curl: {str(e)}")
            return None
    
    def collect_data(self):
        """Collecte les données en utilisant SNMPv3 ou curl comme fallback"""
        # Tentative de collecte via SNMPv3
        data = self.collect_data_snmpv3()
        
        # Si la collecte SNMPv3 échoue, essayer avec curl
        if not data:
            logger.warning("Collecte SNMPv3 échouée, tentative avec curl...")
            data = self.collect_data_curl()
        
        return data
    
    def format_data(self, data):
        """Formate les données collectées pour l'enregistrement"""
        if not data:
            return None
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-4]
        
        # Création d'une ligne de données formatée
        row = [timestamp]
        
        # Ajout des valeurs dans l'ordre des colonnes (en ignorant le timestamp)
        for column in self.column_names[1:]:
            row.append(data.get(column, 0))
        
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
                "metrics": data
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
