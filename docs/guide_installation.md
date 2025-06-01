# Guide d'Installation et d'Utilisation - RCMS_Test
# Auteur: Arthur

## Table des matières
1. [Introduction](#introduction)
2. [Prérequis](#prérequis)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Démarrage](#démarrage)
6. [Utilisation](#utilisation)
7. [Maintenance](#maintenance)
8. [Dépannage](#dépannage)
9. [Sécurité](#sécurité)

## Introduction

Ce document décrit l'installation et l'utilisation de l'infrastructure de monitoring sécurisée RCMS_Test pour la surveillance des balises DME (Distance Measuring Equipment). Cette infrastructure est composée de 5 machines virtuelles Docker, chacune avec un rôle spécifique dans le système global.

## Prérequis

### Matériel recommandé
- CPU: 4 cœurs minimum
- RAM: 8 Go minimum
- Stockage: 20 Go d'espace disque disponible

### Logiciels requis
- Docker Engine (version 20.10.0 ou supérieure)
- Docker Compose (version 2.0.0 ou supérieure)
- Git (pour cloner le dépôt)

## Installation

### 1. Cloner le dépôt
```bash
git clone <url_du_depot> RCMS_Test
cd RCMS_Test
```

### 2. Préparation de l'environnement
Créez les répertoires nécessaires pour les données et les logs :
```bash
mkdir -p data logs/dme_simulator logs/data_collector logs/logstash
```

### 3. Génération des certificats SSL
Pour sécuriser les communications entre les composants, générez les certificats SSL :
```bash
# Créer les répertoires pour les certificats
mkdir -p vm3_elasticsearch/certs vm4_logstash/certs vm5_kibana/certs

# Générer les certificats (exemple simplifié)
cd scripts
./generate_certificates.sh
cd ..
```

## Configuration

### Configuration du simulateur DME (VM1)
Le simulateur DME est préconfiguré pour générer des données simulées. Vous pouvez ajuster les paramètres dans le fichier d'environnement :
```bash
# Créer un fichier .env dans le répertoire vm1_dme_simulator
echo "PORT=5000" > vm1_dme_simulator/.env
echo "HOST=0.0.0.0" >> vm1_dme_simulator/.env
```

### Configuration du collecteur de données (VM2)
Configurez le collecteur pour qu'il pointe vers le simulateur DME :
```bash
# Créer un fichier .env dans le répertoire vm2_data_collector
echo "DME_SIMULATOR_URL=http://dme_simulator:5000" > vm2_data_collector/.env
echo "COLLECTION_INTERVAL=180" >> vm2_data_collector/.env
echo "OUTPUT_FILE=/app/data/dme_data.csv" >> vm2_data_collector/.env
echo "LOGSTASH_ENABLED=true" >> vm2_data_collector/.env
echo "LOGSTASH_HOST=logstash" >> vm2_data_collector/.env
echo "LOGSTASH_PORT=5044" >> vm2_data_collector/.env
```

### Configuration d'Elasticsearch (VM3)
Le fichier `elasticsearch.yml` est déjà configuré. Vous pouvez ajuster les paramètres de mémoire dans le fichier docker-compose.yml selon vos besoins.

### Configuration de Logstash (VM4)
Le pipeline Logstash est préconfiguré pour traiter les données DME. Assurez-vous que les certificats SSL sont correctement placés.

### Configuration de Kibana (VM5)
Kibana est préconfiguré pour se connecter à Elasticsearch. Vous pouvez modifier les paramètres dans le fichier `kibana.yml` si nécessaire.

## Démarrage

### 1. Démarrer l'infrastructure complète
```bash
docker-compose up -d
```

### 2. Vérifier l'état des services
```bash
docker-compose ps
```

### 3. Suivre les logs
```bash
# Tous les services
docker-compose logs -f

# Un service spécifique
docker-compose logs -f dme_simulator
```

## Utilisation

### Accès au simulateur DME (VM1)
- URL: http://localhost:5000
- Points d'accès disponibles:
  - `/health` - Vérification de l'état du service
  - `/oid/<oid>` - Récupération de la valeur d'un OID spécifique
  - `/all` - Récupération de toutes les valeurs DME
  - `/oids` - Liste de tous les OIDs disponibles

### Accès aux données collectées (VM2)
Les données collectées sont stockées dans le fichier CSV à l'emplacement suivant :
```
./data/dme_data.csv
```

### Accès à Elasticsearch (VM3)
- URL: http://localhost:9200
- Identifiants par défaut:
  - Utilisateur: elastic
  - Mot de passe: ChangeMe123!

### Accès à Kibana (VM5)
- URL: http://localhost:5601
- Identifiants par défaut:
  - Utilisateur: elastic
  - Mot de passe: ChangeMe123!

#### Configuration des tableaux de bord Kibana
1. Connectez-vous à Kibana
2. Allez dans "Stack Management" > "Index Patterns"
3. Créez un nouveau modèle d'index avec le motif `rcms-dme-*`
4. Allez dans "Dashboard" et créez un nouveau tableau de bord
5. Ajoutez des visualisations pour surveiller les métriques DME

## Maintenance

### Sauvegarde des données
Pour sauvegarder les données Elasticsearch :
```bash
# Créer un snapshot
curl -X PUT "localhost:9200/_snapshot/my_backup/snapshot_1?wait_for_completion=true" -H "Content-Type: application/json" -d'
{
  "indices": "rcms-dme-*",
  "ignore_unavailable": true,
  "include_global_state": false
}
' -u elastic:ChangeMe123!
```

### Mise à jour des composants
Pour mettre à jour les composants :
```bash
# Arrêter les services
docker-compose down

# Mettre à jour les images
docker-compose pull

# Redémarrer les services
docker-compose up -d
```

## Dépannage

### Problèmes courants et solutions

#### Le simulateur DME ne répond pas
```bash
# Vérifier les logs
docker-compose logs dme_simulator

# Redémarrer le service
docker-compose restart dme_simulator
```

#### Le collecteur ne récupère pas les données
```bash
# Vérifier les logs
docker-compose logs data_collector

# Vérifier la connectivité
docker-compose exec data_collector curl -v dme_simulator:5000/health
```

#### Elasticsearch ne démarre pas
```bash
# Vérifier les logs
docker-compose logs elasticsearch

# Vérifier les permissions
docker-compose exec elasticsearch chown -R elasticsearch:elasticsearch /usr/share/elasticsearch/data
```

## Sécurité

### Changement des mots de passe par défaut
Il est fortement recommandé de changer les mots de passe par défaut :
```bash
# Pour Elasticsearch/Kibana
docker-compose exec elasticsearch bin/elasticsearch-reset-password -u elastic -i
```

### Application du hardening
Pour appliquer les mesures de hardening sur les conteneurs :
```bash
# Exécuter le script de hardening
./hardening/hardening.sh dme_simulator
./hardening/hardening.sh data_collector
./hardening/hardening.sh elasticsearch
./hardening/hardening.sh logstash
./hardening/hardening.sh kibana
```

### Audit de sécurité
Pour effectuer un audit de sécurité de l'infrastructure :
```bash
# Exécuter le script d'audit
./scripts/security_audit.sh
```

---

Pour toute question ou assistance supplémentaire, veuillez contacter l'équipe de support.
