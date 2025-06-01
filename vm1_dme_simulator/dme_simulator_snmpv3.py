#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Simulateur de système DME (Distance Measuring Equipment) avec support SNMPv3
Ce script simule un système DME qui répond à des requêtes SNMPv3 avec des données
simulées pour différents OIDs SNMP.

Auteur: arthur

"""

import os
import time
import random
import logging
import threading
from pysnmp.entity import engine, config
from pysnmp.entity.rfc3413 import cmdrsp, context
from pysnmp.carrier.asyncore.dgram import udp
from pysnmp.proto.api import v2c
from pysnmp.proto import rfc1902

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

# Configuration SNMPv3
def configure_snmpv3_agent():
    """Configure et démarre l'agent SNMPv3"""
    # Création du moteur SNMP
    snmp_engine = engine.SnmpEngine()
    
    # Configuration du transport UDP
    config.addTransport(
        snmp_engine,
        udp.domainName,
        udp.UdpTransport().openServerMode(('0.0.0.0', 161))
    )
    
    # Configuration de l'utilisateur SNMPv3 (USM)
    # authKey est le mot de passe d'authentification, privKey est le mot de passe de chiffrement
    config.addV3User(
        snmp_engine,
        'dmeuser',
        config.usmHMACSHAAuthProtocol,  # Algorithme d'authentification SHA
        'authpassword',                 # Mot de passe d'authentification
        config.usmAesCfb128Protocol,    # Algorithme de chiffrement AES
        'privpassword'                  # Mot de passe de chiffrement
    )
    
    # Configuration des droits d'accès
    config.addVacmUser(
        snmp_engine,
        3,                              # SNMPv3
        'dmeuser',                      # Nom d'utilisateur
        'authPriv',                     # Niveau de sécurité (authentification + chiffrement)
        readSubTree=(1, 3, 6, 1, 4, 1), # OID de base pour les lectures
        writeSubTree=(1, 3, 6, 1, 4, 1) # OID de base pour les écritures
    )
    
    # Création du contexte SNMP
    snmp_context = context.SnmpContext(snmp_engine)
    
    # Enregistrement du gestionnaire de commandes SNMP GET
    cmdrsp.GetCommandResponder(snmp_engine, snmp_context)
    
    # Enregistrement du gestionnaire de commandes SNMP GETNEXT
    cmdrsp.NextCommandResponder(snmp_engine, snmp_context)
    
    # Enregistrement du gestionnaire de commandes SNMP GETBULK
    cmdrsp.BulkCommandResponder(snmp_engine, snmp_context)
    
    # Création de la MIB
    mib_builder = snmp_context.getMibInstrum().getMibBuilder()
    
    # Enregistrement des OIDs et de leurs valeurs
    for oid, name in OID_DESCRIPTIONS.items():
        # Conversion de l'OID en tuple d'entiers
        oid_tuple = tuple(map(int, oid.split('.')))
        
        # Enregistrement de l'OID dans la MIB
        mib_builder.exportSymbols(
            name,
            # Création d'un objet MIB pour cet OID
            v2c.ObjectType(
                v2c.ObjectIdentity(*oid_tuple),
                # La valeur sera mise à jour dynamiquement
                rfc1902.Integer(0)
            ).setMaxAccess('readwrite')
        )
    
    # Fonction de rappel pour les requêtes SNMP GET
    def custom_get_handler(engine, context, varbinds, cb_ctx):
        for oid, val in varbinds:
            # Conversion de l'OID en chaîne de caractères
            oid_str = '.'.join(map(str, oid))
            
            # Récupération de la valeur depuis le générateur de données
            value = dme_generator.get_value_by_oid(oid_str)
            
            if value is not None:
                # Mise à jour de la valeur dans la réponse
                val = rfc1902.Integer(value)
                logger.info(f"Requête SNMP GET pour OID {oid_str}: {value}")
            else:
                logger.warning(f"OID non trouvé: {oid_str}")
        
        return varbinds
    
    # Enregistrement du gestionnaire personnalisé pour les requêtes GET
    cmdrsp.GetCommandResponder(snmp_engine, snmp_context).registerContextName(
        '', custom_get_handler
    )
    
    logger.info("Agent SNMPv3 configuré et démarré sur le port 161")
    
    # Démarrage du moteur SNMP
    snmp_engine.transportDispatcher.jobStarted(1)
    try:
        snmp_engine.transportDispatcher.runDispatcher()
    except:
        snmp_engine.transportDispatcher.closeDispatcher()
        raise

if __name__ == '__main__':
    try:
        # Démarrage du thread de mise à jour des données
        update_thread = threading.Thread(target=update_data_periodically, daemon=True)
        update_thread.start()
        
        # Configuration et démarrage de l'agent SNMPv3
        logger.info("Démarrage du simulateur DME avec SNMPv3")
        configure_snmpv3_agent()
    except KeyboardInterrupt:
        logger.info("Arrêt du simulateur DME")
    except Exception as e:
        logger.critical(f"Erreur critique: {str(e)}")
        exit(1)
