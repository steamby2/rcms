#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de validation de la conformité SNMPv3 et de l'intégration ELK
Ce script vérifie la conformité de l'infrastructure RCMS_Test avec les exigences SNMPv3
et l'intégration avec la suite ELK.

Auteur: arthur

"""

import os
import sys
import json
import yaml
import logging
import subprocess
from pathlib import Path

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("validation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("validation")

class ValidationError(Exception):
    """Exception levée lorsqu'une validation échoue"""
    pass

def check_file_exists(filepath, description):
    """Vérifie si un fichier existe"""
    if not os.path.isfile(filepath):
        raise ValidationError(f"Le fichier {description} n'existe pas: {filepath}")
    logger.info(f"✓ Fichier {description} trouvé: {filepath}")
    return True

def check_directory_exists(dirpath, description):
    """Vérifie si un répertoire existe"""
    if not os.path.isdir(dirpath):
        raise ValidationError(f"Le répertoire {description} n'existe pas: {dirpath}")
    logger.info(f"✓ Répertoire {description} trouvé: {dirpath}")
    return True

def validate_snmpv3_simulator():
    """Valide le simulateur DME SNMPv3"""
    logger.info("Validation du simulateur DME SNMPv3...")
    
    # Vérification des fichiers
    check_file_exists("vm1_dme_simulator/dme_simulator_snmpv3.py", "simulateur DME SNMPv3")
    check_file_exists("vm1_dme_simulator/Dockerfile", "Dockerfile du simulateur")
    check_file_exists("vm1_dme_simulator/requirements.txt", "requirements du simulateur")
    
    # Vérification des dépendances Python
    with open("vm1_dme_simulator/requirements.txt", "r") as f:
        requirements = f.read()
        if "pysnmp" not in requirements:
            raise ValidationError("La bibliothèque pysnmp n'est pas listée dans les dépendances du simulateur")
    
    # Vérification du code source
    with open("vm1_dme_simulator/dme_simulator_snmpv3.py", "r") as f:
        code = f.read()
        if "SNMPv3" not in code:
            raise ValidationError("Le code du simulateur ne mentionne pas SNMPv3")
        if "UsmUserData" not in code and "config.addV3User" not in code:
            raise ValidationError("Le code du simulateur ne configure pas d'utilisateur SNMPv3")
        if "authProtocol" not in code:
            raise ValidationError("Le code du simulateur ne configure pas de protocole d'authentification")
        if "privProtocol" not in code:
            raise ValidationError("Le code du simulateur ne configure pas de protocole de confidentialité")
    
    logger.info("✓ Simulateur DME SNMPv3 validé")
    return True

def validate_snmpv3_collector():
    """Valide le collecteur de données SNMPv3"""
    logger.info("Validation du collecteur de données SNMPv3...")
    
    # Vérification des fichiers
    check_file_exists("vm2_data_collector/dme_collector_snmpv3.py", "collecteur SNMPv3")
    check_file_exists("vm2_data_collector/Dockerfile", "Dockerfile du collecteur")
    check_file_exists("vm2_data_collector/requirements.txt", "requirements du collecteur")
    
    # Vérification des dépendances Python
    with open("vm2_data_collector/requirements.txt", "r") as f:
        requirements = f.read()
        if "pysnmp" not in requirements:
            raise ValidationError("La bibliothèque pysnmp n'est pas listée dans les dépendances du collecteur")
    
    # Vérification du code source
    with open("vm2_data_collector/dme_collector_snmpv3.py", "r") as f:
        code = f.read()
        if "SNMPv3" not in code:
            raise ValidationError("Le code du collecteur ne mentionne pas SNMPv3")
        if "UsmUserData" not in code and "auth_data" not in code:
            raise ValidationError("Le code du collecteur ne configure pas d'authentification SNMPv3")
        if "authProtocol" not in code:
            raise ValidationError("Le code du collecteur ne configure pas de protocole d'authentification")
        if "privProtocol" not in code:
            raise ValidationError("Le code du collecteur ne configure pas de protocole de confidentialité")
    
    logger.info("✓ Collecteur de données SNMPv3 validé")
    return True

def validate_elk_integration():
    """Valide l'intégration avec la suite ELK"""
    logger.info("Validation de l'intégration avec la suite ELK...")
    
    # Vérification des répertoires
    check_directory_exists("vm3_elasticsearch", "configuration Elasticsearch")
    check_directory_exists("vm4_logstash", "configuration Logstash")
    check_directory_exists("vm5_kibana", "configuration Kibana")
    
    # Vérification des fichiers de configuration
    check_file_exists("vm3_elasticsearch/elasticsearch.yml", "configuration Elasticsearch")
    check_file_exists("vm4_logstash/pipeline/dme_pipeline.conf", "pipeline Logstash")
    check_file_exists("vm5_kibana/kibana.yml", "configuration Kibana")
    
    # Vérification de l'intégration dans le collecteur
    with open("vm2_data_collector/dme_collector_snmpv3.py", "r") as f:
        code = f.read()
        if "send_to_logstash" not in code:
            raise ValidationError("Le collecteur ne contient pas de fonction pour envoyer les données à Logstash")
        if "LOGSTASH_ENABLED" not in code:
            raise ValidationError("Le collecteur ne contient pas de configuration pour activer Logstash")
    
    # Vérification de la configuration Logstash
    with open("vm4_logstash/pipeline/dme_pipeline.conf", "r") as f:
        config = f.read()
        if "input {" not in config:
            raise ValidationError("La configuration Logstash ne contient pas de section input")
        if "filter {" not in config:
            raise ValidationError("La configuration Logstash ne contient pas de section filter")
        if "output {" not in config:
            raise ValidationError("La configuration Logstash ne contient pas de section output")
        if "elasticsearch" not in config:
            raise ValidationError("La configuration Logstash ne contient pas de sortie vers Elasticsearch")
    
    logger.info("✓ Intégration avec la suite ELK validée")
    return True

def validate_docker_compose():
    """Valide le fichier docker-compose.yml"""
    logger.info("Validation du fichier docker-compose.yml...")
    
    # Vérification du fichier
    check_file_exists("docker-compose.yml", "docker-compose.yml")
    
    # Chargement du fichier
    with open("docker-compose.yml", "r") as f:
        try:
            compose = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValidationError(f"Erreur de syntaxe dans le fichier docker-compose.yml: {str(e)}")
    
    # Vérification des services
    required_services = ["dme_simulator", "data_collector", "elasticsearch", "logstash", "kibana"]
    for service in required_services:
        if service not in compose.get("services", {}):
            raise ValidationError(f"Le service {service} n'est pas défini dans docker-compose.yml")
    
    # Vérification des configurations SNMPv3
    dme_simulator = compose["services"]["dme_simulator"]
    if "environment" not in dme_simulator:
        raise ValidationError("Le service dme_simulator n'a pas de variables d'environnement")
    
    env_vars = {var.split("=")[0]: var.split("=")[1] for var in dme_simulator.get("environment", []) if "=" in var}
    required_env_vars = ["SNMP_USER", "SNMP_AUTH_PROTOCOL", "SNMP_AUTH_PASSWORD", "SNMP_PRIV_PROTOCOL", "SNMP_PRIV_PASSWORD"]
    for var in required_env_vars:
        if var not in env_vars:
            raise ValidationError(f"La variable d'environnement {var} n'est pas définie pour dme_simulator")
    
    # Vérification des ports
    if "ports" not in dme_simulator:
        raise ValidationError("Le service dme_simulator n'expose pas de ports")
    
    ports = [str(port) for port in dme_simulator.get("ports", [])]
    if not any("161" in port for port in ports):
        raise ValidationError("Le port SNMP (161) n'est pas exposé pour dme_simulator")
    
    # Vérification de la sécurité
    if "user" not in dme_simulator:
        raise ValidationError("Le service dme_simulator n'est pas configuré pour s'exécuter en tant qu'utilisateur non-root")
    
    if "cap_drop" not in dme_simulator:
        raise ValidationError("Le service dme_simulator n'a pas de configuration cap_drop pour limiter les capacités")
    
    logger.info("✓ Fichier docker-compose.yml validé")
    return True

def validate_documentation():
    """Valide la documentation"""
    logger.info("Validation de la documentation...")
    
    # Vérification des fichiers
    check_file_exists("README.md", "README")
    check_directory_exists("docs", "documentation")
    check_file_exists("docs/architecture.md", "documentation d'architecture")
    check_file_exists("docs/guide_installation.md", "guide d'installation")
    check_file_exists("docs/rapport_securite.md", "rapport de sécurité")
    check_file_exists("docs/guide_snmpv3.md", "guide SNMPv3")
    
    # Vérification du contenu du README
    with open("README.md", "r") as f:
        readme = f.read()
        if "SNMPv3" not in readme:
            raise ValidationError("Le README ne mentionne pas SNMPv3")
        if "Ubuntu 24" not in readme and "environnement virtualisé" not in readme:
            raise ValidationError("Le README ne mentionne pas les contraintes d'environnement Python/Ubuntu 24")
    
    # Vérification du guide SNMPv3
    with open("docs/guide_snmpv3.md", "r") as f:
        guide = f.read()
        if "authentification" not in guide.lower():
            raise ValidationError("Le guide SNMPv3 ne mentionne pas l'authentification")
        if "chiffrement" not in guide.lower():
            raise ValidationError("Le guide SNMPv3 ne mentionne pas le chiffrement")
        if "confidentialité" not in guide.lower():
            raise ValidationError("Le guide SNMPv3 ne mentionne pas la confidentialité")
    
    logger.info("✓ Documentation validée")
    return True

def validate_hardening():
    """Valide les scripts de hardening"""
    logger.info("Validation des scripts de hardening...")
    
    # Vérification des fichiers
    check_directory_exists("hardening", "scripts de hardening")
    check_file_exists("hardening/hardening.sh", "script de hardening")
    
    # Vérification du contenu du script
    with open("hardening/hardening.sh", "r") as f:
        script = f.read()
        if "ufw" not in script:
            raise ValidationError("Le script de hardening ne configure pas le pare-feu UFW")
        if "fail2ban" not in script:
            raise ValidationError("Le script de hardening ne configure pas Fail2ban")
        if "sshd_config" not in script:
            raise ValidationError("Le script de hardening ne configure pas SSH")
    
    logger.info("✓ Scripts de hardening validés")
    return True

def run_validation():
    """Exécute toutes les validations"""
    try:
        logger.info("Début de la validation de l'infrastructure RCMS_Test")
        
        validate_snmpv3_simulator()
        validate_snmpv3_collector()
        validate_elk_integration()
        validate_docker_compose()
        validate_documentation()
        validate_hardening()
        
        logger.info("✓ Validation complète: l'infrastructure RCMS_Test est conforme aux exigences")
        return True
    except ValidationError as e:
        logger.error(f"❌ Validation échouée: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"❌ Erreur inattendue lors de la validation: {str(e)}")
        return False

if __name__ == "__main__":
    success = run_validation()
    sys.exit(0 if success else 1)
