#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Vrai agent SNMPv3 DME utilisant pysnmp
Expose tous les OIDs DME sur le port 161 UDP avec authentification et chiffrement
Auteur: arthur
"""

import os
import time
import random
import logging
import threading
from datetime import datetime
from pysnmp.entity import engine, config
from pysnmp.entity.rfc3413 import cmdrsp, context
from pysnmp.carrier.asyncore.dgram import udp
from pysnmp.proto.api import v2c
from pysnmp.smi import builder, view, rfc1902, instrum

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

# OIDs DME et leurs valeurs initiales
DME_OIDS = {
    "1.3.6.1.4.1.32275.2.1.2.2.5.10": {"name": "mtuExecTXPADelayCurrentValue-0", "value": 0},
    "1.3.6.1.4.1.32275.2.1.2.2.5.34": {"name": "mtuExecTXPBDelayCurrentValue-0", "value": 49200},
    "1.3.6.1.4.1.32275.2.1.2.2.8.10": {"name": "mtuExecTXPADelayCurrentValue-3", "value": 0},
    "1.3.6.1.4.1.32275.2.1.2.2.8.34": {"name": "mtuExecTXPBDelayCurrentValue-3", "value": 49200},
    "1.3.6.1.4.1.32275.2.1.2.2.5.11": {"name": "mtuExecTXPAPulsePairSpacing-0", "value": 0},
    "1.3.6.1.4.1.32275.2.1.2.2.5.35": {"name": "mtuExecTXPBPulsePairSpacing-0", "value": 12000},
    "1.3.6.1.4.1.32275.2.1.2.2.8.11": {"name": "mtuExecTXPAPulsePairSpacing-3", "value": 0},
    "1.3.6.1.4.1.32275.2.1.2.2.8.35": {"name": "mtuExecTXPBPulsePairSpacing-3", "value": 12000},
    "1.3.6.1.4.1.32275.2.1.2.2.5.12": {"name": "mtuExecTXPATransmittedPowerCurrentValue-0", "value": 0},
    "1.3.6.1.4.1.32275.2.1.2.2.5.36": {"name": "mtuExecTXPBTransmittedPowerCurrentValue-0", "value": 1080},
    "1.3.6.1.4.1.32275.2.1.2.2.8.12": {"name": "mtuExecTXPATransmittedPowerCurrentValue-3", "value": 0},
    "1.3.6.1.4.1.32275.2.1.2.2.8.36": {"name": "mtuExecTXPBTransmittedPowerCurrentValue-3", "value": 1125},
    "1.3.6.1.4.1.32275.2.1.2.2.5.13": {"name": "mtuExecTXPAEfficiency-0", "value": 0},
    "1.3.6.1.4.1.32275.2.1.2.2.5.37": {"name": "mtuExecTXPBEfficiency-0", "value": 90},
    "1.3.6.1.4.1.32275.2.1.2.2.8.13": {"name": "mtuExecTXPAEfficiency-3", "value": 0},
    "1.3.6.1.4.1.32275.2.1.2.2.8.37": {"name": "mtuExecTXPBEfficiency-3", "value": 91},
    "1.3.6.1.4.1.32275.2.1.2.2.5.14": {"name": "mtuExecTXPATxFreqError-0", "value": 0},
    "1.3.6.1.4.1.32275.2.1.2.2.5.38": {"name": "mtuExecTXPBTxFreqError-0", "value": 2},
    "1.3.6.1.4.1.32275.2.1.2.2.8.14": {"name": "mtuExecTXPATxFreqError-3", "value": 0},
    "1.3.6.1.4.1.32275.2.1.2.2.8.38": {"name": "mtuExecTXPBTxFreqError-3", "value": 2},
    "1.3.6.1.4.1.32275.2.1.2.2.5.15": {"name": "mtuExecRadiatedPowerCurrentValue-0", "value": 980},
    "1.3.6.1.4.1.32275.2.1.2.2.8.15": {"name": "mtuExecRadiatedPowerCurrentValue-3", "value": 970},
    "1.3.6.1.4.1.32275.2.1.2.2.5.16": {"name": "mtuExecTransmissionRate-0", "value": 840},
    "1.3.6.1.4.1.32275.2.1.2.2.8.16": {"name": "mtuExecTransmissionRate-3", "value": 840},
    "1.3.6.1.4.1.32275.2.1.2.2.5.17": {"name": "mtuExecIdentStatus-0", "value": 1},
    "1.3.6.1.4.1.32275.2.1.2.2.8.17": {"name": "mtuExecIdentStatus-3", "value": 1},
}

class DMESNMPAgent:
    def __init__(self):
        self.snmp_engine = engine.SnmpEngine()
        self.mib_builder = self.snmp_engine.getMibBuilder()
        self.mib_instrum = instrum.MibInstrumController(self.mib_builder)
        self.oid_instances = {}
        self.lock = threading.Lock()
        
    def setup_snmpv3(self):
        """Configure SNMPv3 avec authentification et chiffrement"""
        logger.info("Configuration de l'agent SNMPv3...")
        
        # Transport UDP
        config.addTransport(
            self.snmp_engine,
            udp.domainName + (1,),
            udp.UdpTransport().openServerMode(('0.0.0.0', 161))
        )
        
        # Utilisateur SNMPv3
        config.addV3User(
            self.snmp_engine,
            SNMP_USER,
            config.usmHMACSHAAuthProtocol, SNMP_AUTH_PASSWORD,
            config.usmAesCfb128Protocol, SNMP_PRIV_PASSWORD
        )
        
        # Droits d'accès
        config.addVacmUser(
            self.snmp_engine, 3, SNMP_USER, 'authPriv', (1, 3, 6, 1, 4, 1, 32275), (1, 3, 6, 1, 4, 1, 32275)
        )
        
        logger.info(f"SNMPv3 configuré pour l'utilisateur: {SNMP_USER}")
        
    def setup_mib(self):
        """Configure la MIB avec tous les OIDs DME"""
        logger.info("Configuration de la MIB DME...")

        for oid_str, oid_data in DME_OIDS.items():
            oid_tuple = tuple(int(x) for x in oid_str.split('.'))

            MibScalar, MibScalarInstance = self.mib_builder.importSymbols(
                'SNMPv2-SMI', 'MibScalar', 'MibScalarInstance'
            )

            scalar = MibScalar(oid_tuple, rfc1902.Integer32()).setMaxAccess('readonly')
            instance = MibScalarInstance(oid_tuple, (0,), rfc1902.Integer32(oid_data['value']))
            self.mib_builder.exportSymbols(f'DME-MIB-{oid_data["name"]}', scalar, instance)
            self.oid_instances[oid_str] = instance

        self.snmp_context = context.SnmpContext(self.snmp_engine)
        cmdrsp.GetCommandResponder(self.snmp_engine, self.snmp_context)
        cmdrsp.NextCommandResponder(self.snmp_engine, self.snmp_context)

        logger.info(f"MIB configurée avec {len(DME_OIDS)} OIDs")
        
    def get_oid_value(self, oid_str):
        """Retourne la valeur actuelle d'un OID"""
        with self.lock:
            if oid_str in DME_OIDS:
                return DME_OIDS[oid_str]["value"]
            return None
            
    def update_values(self):
        """Met à jour les valeurs des OIDs avec de légères variations"""
        with self.lock:
            # Variation des délais
            DME_OIDS["1.3.6.1.4.1.32275.2.1.2.2.5.34"]["value"] += random.randint(-50, 50)
            DME_OIDS["1.3.6.1.4.1.32275.2.1.2.2.8.34"]["value"] += random.randint(-50, 50)
            
            # Variation de la puissance
            DME_OIDS["1.3.6.1.4.1.32275.2.1.2.2.5.36"]["value"] += random.randint(-5, 5)
            DME_OIDS["1.3.6.1.4.1.32275.2.1.2.2.8.36"]["value"] += random.randint(-5, 5)
            
            # Variation de l'efficacité
            DME_OIDS["1.3.6.1.4.1.32275.2.1.2.2.5.37"]["value"] += random.randint(-2, 2)
            DME_OIDS["1.3.6.1.4.1.32275.2.1.2.2.8.37"]["value"] += random.randint(-2, 2)
            
            # Normaliser les valeurs
            self._normalize_values()

            # Mettre à jour les instances MIB
            for oid_str, instance in self.oid_instances.items():
                instance.setValue(rfc1902.Integer32(DME_OIDS[oid_str]["value"]))
            
    def _normalize_values(self):
        """Maintient les valeurs dans des plages raisonnables"""
        # Délais
        DME_OIDS["1.3.6.1.4.1.32275.2.1.2.2.5.34"]["value"] = max(49000, min(49400, DME_OIDS["1.3.6.1.4.1.32275.2.1.2.2.5.34"]["value"]))
        DME_OIDS["1.3.6.1.4.1.32275.2.1.2.2.8.34"]["value"] = max(49000, min(49400, DME_OIDS["1.3.6.1.4.1.32275.2.1.2.2.8.34"]["value"]))
        
        # Puissance
        DME_OIDS["1.3.6.1.4.1.32275.2.1.2.2.5.36"]["value"] = max(1050, min(1100, DME_OIDS["1.3.6.1.4.1.32275.2.1.2.2.5.36"]["value"]))
        DME_OIDS["1.3.6.1.4.1.32275.2.1.2.2.8.36"]["value"] = max(1100, min(1150, DME_OIDS["1.3.6.1.4.1.32275.2.1.2.2.8.36"]["value"]))
        
        # Efficacité
        DME_OIDS["1.3.6.1.4.1.32275.2.1.2.2.5.37"]["value"] = max(85, min(95, DME_OIDS["1.3.6.1.4.1.32275.2.1.2.2.5.37"]["value"]))
        DME_OIDS["1.3.6.1.4.1.32275.2.1.2.2.8.37"]["value"] = max(85, min(95, DME_OIDS["1.3.6.1.4.1.32275.2.1.2.2.8.37"]["value"]))
    
    def start_agent(self):
        """Démarre l'agent SNMP"""
        logger.info("Démarrage de l'agent SNMPv3 DME...")
        
        # Configuration
        self.setup_snmpv3()
        self.setup_mib()
        
        # Thread de mise à jour des valeurs
        def update_thread():
            while True:
                time.sleep(30)  # Mise à jour toutes les 30 secondes
                self.update_values()
                logger.debug("Valeurs DME mises à jour")
        
        update_thread_obj = threading.Thread(target=update_thread, daemon=True)
        update_thread_obj.start()
        
        # Démarrer l'agent
        logger.info("Agent SNMPv3 démarré sur le port 161")
        logger.info("Prêt à recevoir des requêtes SNMPv3...")
        
        # Boucle principale
        try:
            self.snmp_engine.transportDispatcher.jobStarted(1)
            self.snmp_engine.transportDispatcher.runDispatcher()
        except Exception as e:
            logger.error(f"Erreur agent SNMP: {str(e)}")
            raise

if __name__ == '__main__':
    try:
        agent = DMESNMPAgent()
        agent.start_agent()
    except KeyboardInterrupt:
        logger.info("Arrêt de l'agent SNMPv3")
    except Exception as e:
        logger.critical(f"Erreur critique: {str(e)}")
        exit(1)
