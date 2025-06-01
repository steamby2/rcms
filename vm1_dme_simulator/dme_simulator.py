#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simulateur de système DME (Distance Measuring Equipment)
Ce script simule un système DME qui répond à des requêtes HTTP avec des données
simulées pour différents OIDs SNMP.

Auteur: arthur

"""

import os
import time
import random
import logging
import json
from datetime import datetime
from flask import Flask, request, jsonify, Response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import threading

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("dme_simulator.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("dme_simulator")

# Initialisation de l'application Flask
app = Flask(__name__)

# Configuration du limiteur de requêtes pour prévenir les attaques DoS
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

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
        """Met à jour les données avec de légères variations pour simuler des changements réels"""
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
            
            # Variation des erreurs de fréquence (±1)
            self.data["mtuExecTXPBTxFreqError-0"] += random.randint(-1, 1)
            self.data["mtuExecTXPBTxFreqError-3"] += random.randint(-1, 1)
            
            # Variation de la puissance rayonnée (±10)
            self.data["mtuExecRadiatedPowerCurrentValue-0"] += random.randint(-10, 10)
            self.data["mtuExecRadiatedPowerCurrentValue-3"] += random.randint(-10, 10)
            
            # Variation du taux de transmission (±5)
            self.data["mtuExecTransmissionRate-0"] += random.randint(-5, 5)
            self.data["mtuExecTransmissionRate-3"] += random.randint(-5, 5)
            
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
        
        # Normalisation des erreurs de fréquence
        self.data["mtuExecTXPBTxFreqError-0"] = max(0, min(5, self.data["mtuExecTXPBTxFreqError-0"]))
        self.data["mtuExecTXPBTxFreqError-3"] = max(0, min(5, self.data["mtuExecTXPBTxFreqError-3"]))
        
        # Normalisation de la puissance rayonnée
        self.data["mtuExecRadiatedPowerCurrentValue-0"] = max(950, min(1010, self.data["mtuExecRadiatedPowerCurrentValue-0"]))
        self.data["mtuExecRadiatedPowerCurrentValue-3"] = max(950, min(1010, self.data["mtuExecRadiatedPowerCurrentValue-3"]))
        
        # Normalisation du taux de transmission
        self.data["mtuExecTransmissionRate-0"] = max(820, min(860, self.data["mtuExecTransmissionRate-0"]))
        self.data["mtuExecTransmissionRate-3"] = max(820, min(860, self.data["mtuExecTransmissionRate-3"]))
    
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

# Fonction pour mettre à jour périodiquement les données
def update_data_periodically():
    """Met à jour les données DME toutes les 3 minutes"""
    while True:
        time.sleep(180)  # 3 minutes
        dme_generator.update_data()
        logger.info("Données DME mises à jour")

# Démarrage du thread de mise à jour des données
update_thread = threading.Thread(target=update_data_periodically, daemon=True)
update_thread.start()

@app.route('/health', methods=['GET'])
def health_check():
    """Point de terminaison pour vérifier l'état du service"""
    return jsonify({"status": "ok", "timestamp": datetime.now().isoformat()})

@app.route('/oid/<path:oid>', methods=['GET'])
@limiter.limit("30 per minute")
def get_oid_value(oid):
    """Point de terminaison pour récupérer la valeur d'un OID spécifique"""
    # Journalisation de la requête
    logger.info(f"Requête reçue pour OID: {oid} depuis {request.remote_addr}")
    
    # Vérification de l'authentification (à implémenter selon les besoins)
    # if not is_authenticated(request):
    #     logger.warning(f"Tentative d'accès non autorisé depuis {request.remote_addr}")
    #     return jsonify({"error": "Non autorisé"}), 401
    
    # Récupération de la valeur
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
@limiter.limit("10 per minute")
def get_all_values():
    """Point de terminaison pour récupérer toutes les valeurs DME"""
    # Journalisation de la requête
    logger.info(f"Requête reçue pour toutes les valeurs depuis {request.remote_addr}")
    
    # Récupération de toutes les données
    data = dme_generator.get_data()
    
    # Ajout du timestamp
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

@app.errorhandler(429)
def ratelimit_handler(e):
    """Gestionnaire pour les erreurs de limitation de taux"""
    logger.warning(f"Limite de taux dépassée par {request.remote_addr}")
    return jsonify({"error": "Trop de requêtes, veuillez réessayer plus tard"}), 429

@app.errorhandler(Exception)
def handle_exception(e):
    """Gestionnaire global d'exceptions"""
    logger.error(f"Erreur non gérée: {str(e)}")
    return jsonify({"error": "Une erreur interne s'est produite"}), 500

if __name__ == '__main__':
    # Configuration du port et de l'hôte
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    # Démarrage du serveur en mode sécurisé (à configurer avec SSL en production)
    logger.info(f"Démarrage du simulateur DME sur {host}:{port}")
    app.run(host=host, port=port, debug=False)
