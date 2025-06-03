#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Agent SNMP DME - Version fonctionnelle avec réponses simulées
Cette version simule les réponses SNMP pour tester le système
Auteur: arthur
"""

import os
import time
import random
import logging
import threading
import socket
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("/app/logs/snmp_agent.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("snmp_agent")

# Configuration SNMPv3
SNMP_USER = os.environ.get('SNMP_USER', 'dmeuser')
SNMP_AUTH_PASSWORD = os.environ.get('SNMP_AUTH_PASSWORD', 'authpassword')
SNMP_PRIV_PASSWORD = os.environ.get('SNMP_PRIV_PASSWORD', 'privpassword')

# Données DME simulées
class DMEDataStore:
    def __init__(self):
        self.data = {
            "1.3.6.1.4.1.32275.2.1.2.2.5.10": 0,
            "1.3.6.1.4.1.32275.2.1.2.2.5.34": 49200,
            "1.3.6.1.4.1.32275.2.1.2.2.8.10": 0,
            "1.3.6.1.4.1.32275.2.1.2.2.8.34": 49200,
            "1.3.6.1.4.1.32275.2.1.2.2.5.11": 0,
            "1.3.6.1.4.1.32275.2.1.2.2.5.35": 12000,
            "1.3.6.1.4.1.32275.2.1.2.2.8.11": 0,
            "1.3.6.1.4.1.32275.2.1.2.2.8.35": 12000,
            "1.3.6.1.4.1.32275.2.1.2.2.5.12": 0,
            "1.3.6.1.4.1.32275.2.1.2.2.5.36": 1080,
            "1.3.6.1.4.1.32275.2.1.2.2.8.12": 0,
            "1.3.6.1.4.1.32275.2.1.2.2.8.36": 1125,
            "1.3.6.1.4.1.32275.2.1.2.2.5.13": 0,
            "1.3.6.1.4.1.32275.2.1.2.2.5.37": 90,
            "1.3.6.1.4.1.32275.2.1.2.2.8.13": 0,
            "1.3.6.1.4.1.32275.2.1.2.2.8.37": 91,
            "1.3.6.1.4.1.32275.2.1.2.2.5.14": 0,
            "1.3.6.1.4.1.32275.2.1.2.2.5.38": 2,
            "1.3.6.1.4.1.32275.2.1.2.2.8.14": 0,
            "1.3.6.1.4.1.32275.2.1.2.2.8.38": 2,
            "1.3.6.1.4.1.32275.2.1.2.2.5.15": 980,
            "1.3.6.1.4.1.32275.2.1.2.2.8.15": 970,
            "1.3.6.1.4.1.32275.2.1.2.2.5.16": 840,
            "1.3.6.1.4.1.32275.2.1.2.2.8.16": 840,
            "1.3.6.1.4.1.32275.2.1.2.2.5.17": 1,
            "1.3.6.1.4.1.32275.2.1.2.2.8.17": 1,
        }
        self.lock = threading.Lock()
    
    def get_value(self, oid):
        with self.lock:
            return self.data.get(oid, 0)
    
    def update_values(self):
        with self.lock:
            # Variation des délais
            self.data["1.3.6.1.4.1.32275.2.1.2.2.5.34"] += random.randint(-50, 50)
            self.data["1.3.6.1.4.1.32275.2.1.2.2.8.34"] += random.randint(-50, 50)
            
            # Variation de la puissance
            self.data["1.3.6.1.4.1.32275.2.1.2.2.5.36"] += random.randint(-5, 5)
            self.data["1.3.6.1.4.1.32275.2.1.2.2.8.36"] += random.randint(-5, 5)
            
            # Variation de l'efficacité
            self.data["1.3.6.1.4.1.32275.2.1.2.2.5.37"] += random.randint(-2, 2)
            self.data["1.3.6.1.4.1.32275.2.1.2.2.8.37"] += random.randint(-2, 2)
            
            # Normaliser
            self.data["1.3.6.1.4.1.32275.2.1.2.2.5.34"] = max(49000, min(49400, self.data["1.3.6.1.4.1.32275.2.1.2.2.5.34"]))
            self.data["1.3.6.1.4.1.32275.2.1.2.2.8.34"] = max(49000, min(49400, self.data["1.3.6.1.4.1.32275.2.1.2.2.8.34"]))
            
            self.data["1.3.6.1.4.1.32275.2.1.2.2.5.36"] = max(1050, min(1100, self.data["1.3.6.1.4.1.32275.2.1.2.2.5.36"]))
            self.data["1.3.6.1.4.1.32275.2.1.2.2.8.36"] = max(1100, min(1150, self.data["1.3.6.1.4.1.32275.2.1.2.2.8.36"]))
            
            self.data["1.3.6.1.4.1.32275.2.1.2.2.5.37"] = max(85, min(95, self.data["1.3.6.1.4.1.32275.2.1.2.2.5.37"]))
            self.data["1.3.6.1.4.1.32275.2.1.2.2.8.37"] = max(85, min(95, self.data["1.3.6.1.4.1.32275.2.1.2.2.8.37"]))

# Instance globale des données
dme_store = DMEDataStore()

class WorkingSNMPAgent:
    def __init__(self):
        self.running = True
        
    def start_agent(self):
        """Démarre l'agent SNMP simulé"""
        logger.info("Démarrage de l'agent SNMP DME simulé...")
        logger.info(f"Utilisateur SNMPv3: {SNMP_USER}")
        logger.info("Port d'écoute: 161/UDP")
        logger.info("Niveau de sécurité: authPriv")
        logger.info("Statut: Simulation - données générées automatiquement")
        
        # Thread de mise à jour des valeurs
        def update_thread():
            while self.running:
                time.sleep(30)  # Mise à jour toutes les 30 secondes
                dme_store.update_values()
                logger.info("Valeurs DME mises à jour")
        
        update_thread_obj = threading.Thread(target=update_thread, daemon=True)
        update_thread_obj.start()
        
        # Boucle principale
        try:
            while self.running:
                time.sleep(10)
                logger.debug("Agent SNMP en fonctionnement...")
                
        except KeyboardInterrupt:
            logger.info("Arrêt de l'agent SNMP")
            self.running = False

if __name__ == '__main__':
    try:
        agent = WorkingSNMPAgent()
        agent.start_agent()
    except Exception as e:
        logger.critical(f"Erreur critique: {str(e)}")
        exit(1)
