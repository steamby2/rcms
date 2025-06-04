# RCMS_Test - Infrastructure de Monitoring Sécurisée pour DME

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg) ![License](https://img.shields.io/badge/license-MIT-green.svg) ![Docker](https://img.shields.io/badge/docker-required-blue.svg) ![Status](https://img.shields.io/badge/status-production--ready-green.svg)

## 📋 Table des matières

- [Vue d'ensemble](https://claude.ai/chat/9ee2308c-bdb4-4052-8d32-1287189c40d3#vue-densemble)
- [Architecture](https://claude.ai/chat/9ee2308c-bdb4-4052-8d32-1287189c40d3#architecture)
- [Prérequis](https://claude.ai/chat/9ee2308c-bdb4-4052-8d32-1287189c40d3#prérequis)
- [Installation](https://claude.ai/chat/9ee2308c-bdb4-4052-8d32-1287189c40d3#installation)
- [Configuration](https://claude.ai/chat/9ee2308c-bdb4-4052-8d32-1287189c40d3#configuration)
- [Utilisation](https://claude.ai/chat/9ee2308c-bdb4-4052-8d32-1287189c40d3#utilisation)
- [Gestion de la persistance](https://claude.ai/chat/9ee2308c-bdb4-4052-8d32-1287189c40d3#gestion-de-la-persistance)
- [Monitoring et surveillance](https://claude.ai/chat/9ee2308c-bdb4-4052-8d32-1287189c40d3#monitoring-et-surveillance)
- [Sécurité](https://claude.ai/chat/9ee2308c-bdb4-4052-8d32-1287189c40d3#sécurité)
- [Dépannage](https://claude.ai/chat/9ee2308c-bdb4-4052-8d32-1287189c40d3#dépannage)
- [Scripts utiles](https://claude.ai/chat/9ee2308c-bdb4-4052-8d32-1287189c40d3#scripts-utiles)
- [API Reference](https://claude.ai/chat/9ee2308c-bdb4-4052-8d32-1287189c40d3#api-reference)
- [Contribution](https://claude.ai/chat/9ee2308c-bdb4-4052-8d32-1287189c40d3#contribution)

## 🎯 Vue d'ensemble

RCMS_Test est une infrastructure de monitoring sécurisée pour la surveillance en temps réel des balises DME (Distance Measuring Equipment) utilisées dans la sécurité aérienne.

L'infrastructure utilise une architecture microservices basée sur Docker avec la stack ELK (Elasticsearch, Logstash, Kibana) pour la collecte, le traitement et la visualisation des données de monitoring.

### ✨ Fonctionnalités principales

- 🛡️ **Sécurité renforcée** avec SNMPv3 (authentification + chiffrement)
- 📊 **Monitoring temps réel** avec collecte toutes les 3 minutes
- 🔄 **Persistance des données** avec volumes Docker et sauvegarde CSV
- 📈 **Dashboards interactifs** pour visualisation des métriques DME
- 🚀 **Déploiement containerisé** avec Docker Compose
- 🔍 **Alertes et notifications** via Kibana
- 💾 **Sauvegarde automatique** locale et Elasticsearch

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   VM1: DME      │    │   VM2: Data     │    │   VM3:          │
│   Simulator     │◄──►│   Collector     │◄──►│   Elasticsearch │
│   (SNMPv3)      │    │   (SNMPv3)      │    │   (Storage)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       ▲
                                ▼                       │
┌─────────────────┐    ┌─────────────────┐             │
│   VM5: Kibana   │◄──►│   VM4: Logstash │─────────────┘
│   (Dashboard)   │    │   (Processing)  │
└─────────────────┘    └─────────────────┘
```

### 🎛️ Composants

| Service            | Rôle                  | Port                   | Technologie           |
| ------------------ | --------------------- | ---------------------- | --------------------- |
| **DME Simulator**  | Simulation balise DME | 161 (SNMP), 5000 (API) | Python, Flask, SNMPv3 |
| **Data Collector** | Collecte données      | -                      | Python, pysnmp        |
| **Elasticsearch**  | Stockage/Indexation   | 9200, 9300             | Elasticsearch 7.14.0  |
| **Logstash**       | Traitement données    | 5044, 9600             | Logstash 7.14.0       |
| **Kibana**         | Visualisation         | 5601                   | Kibana 7.14.0         |

## 🔧 Prérequis

### Matériel recommandé

- **CPU**: 4 cœurs minimum
- **RAM**: 8 Go minimum
- **Stockage**: 20 Go d'espace disque disponible

### Logiciels requis

- **Docker Engine** (version 20.10.0+)
- **Docker Compose** (version 2.0.0+)
- **Git** (pour cloner le dépôt)

### Systèmes supportés

- ✅ Linux (Ubuntu 20.04+, CentOS 8+)
- ✅ Windows 10/11 avec Docker Desktop
- ✅ macOS avec Docker Desktop

## 🚀 Installation

### 1. Cloner le dépôt

```bash
git clone <url_du_depot> RCMS_Test
cd RCMS_Test
```

### 2. Préparer l'environnement

```bash
# Créer les répertoires nécessaires
mkdir -p data logs/dme_simulator logs/data_collector logs/logstash

# Créer les répertoires pour les certificats SSL
mkdir -p vm3_elasticsearch/certs vm4_logstash/certs vm5_kibana/certs
```

### 3. Configuration initiale

```bash
# Copier le fichier de configuration par défaut
cp docker-compose.yml.example docker-compose.yml

# Ajuster les mots de passe par défaut (RECOMMANDÉ)
nano secrets/elastic_password.txt
```

### 4. Démarrage

```bash
# Démarrer l'infrastructure complète
docker-compose up -d

# Vérifier l'état des services
docker-compose ps
```

## ⚙️ Configuration

### Variables d'environnement

Le collecteur de données utilise les variables suivantes :

```bash
# Configuration DME
DME_SIMULATOR_URL=http://dme_simulator:5000
COLLECTION_INTERVAL=180  # 3 minutes

# Configuration SNMPv3
SNMP_USER=dmeuser
SNMP_AUTH_PASSWORD=authpassword
SNMP_PRIV_PASSWORD=privpassword

# Configuration Logstash
LOGSTASH_ENABLED=true
LOGSTASH_HOST=logstash
LOGSTASH_PORT=5044
```

### Sécurité par défaut

| Service           | Utilisateur | Mot de passe                    | Notes                        |
| ----------------- | ----------- | ------------------------------- | ---------------------------- |
| **Elasticsearch** | `elastic`   | `SuperAdmin123!`                | À changer en production      |
| **Kibana**        | `elastic`   | `SuperAdmin123!`                | Même compte qu'Elasticsearch |
| **SNMPv3**        | `dmeuser`   | `authpassword` / `privpassword` | Protocoles SHA/AES           |

## 🎮 Utilisation

### Accès aux interfaces

| Service           | URL                   | Identifiants           |
| ----------------- | --------------------- | ---------------------- |
| **Kibana**        | http://localhost:5601 | elastic/SuperAdmin123! |
| **Elasticsearch** | http://localhost:9200 | elastic/SuperAdmin123! |
| **DME Simulator** | http://localhost:5000 | -                      |
| **Logstash**      | http://localhost:9600 | -                      |

### Première connexion Kibana

1. **Ouvrir Kibana**: http://localhost:5601
2. **Se connecter** avec `elastic` / `SuperAdmin123!`
3. **Créer l'index pattern** : `rcms-dme-*`
4. **Accéder aux dashboards** : Menu → Dashboard → "Monitoring DME - RCMS Production"

### Métriques surveillées

Le système collecte automatiquement ces métriques DME :

- 📡 **Délais de transmission** (TXP A/B pour canaux 0 et 3)
- ⚡ **Puissance transmise** (valeurs actuelles)
- 📊 **Efficacité des transmetteurs** (%)
- 🔧 **Erreurs de fréquence** (Hz)
- 📈 **Puissance rayonnée** (W)
- 🔄 **Taux de transmission** (Hz)
- ✅ **Statut d'identification**

## 💾 Gestion de la persistance

### Arrêt propre

```bash
# Méthode recommandée (préserve TOUTES les données)
docker-compose down

# Méthode progressive (ultra-sécurisée)
docker-compose stop data_collector
docker-compose stop kibana
docker-compose stop logstash
docker-compose stop elasticsearch
docker-compose stop dme_simulator
```

### Redémarrage

```bash
# Redémarrage normal
docker-compose up -d

# Redémarrage avec rebuild
docker-compose up -d --build
```

### Vérification de la persistance

```bash
# Vérifier les volumes (données)
docker volume ls | grep rcms

# Vérifier les données Elasticsearch
curl -u "elastic:SuperAdmin123!" "http://localhost:9200/rcms-dme-*/_count"

# Vérifier les fichiers CSV locaux
ls -la data/dme_data.csv
```

## 📊 Monitoring et surveillance

### Logs en temps réel

```bash
# Tous les services
docker-compose logs -f

# Service spécifique
docker-compose logs -f data_collector
docker-compose logs -f elasticsearch
```

### Métriques système

```bash
# État des services
docker-compose ps

# Utilisation des ressources
docker stats

# Espace disque des volumes
docker system df
```

### Scripts de monitoring

Le projet inclut plusieurs scripts utiles :

```bash
# Test de persistance complet
./test_persistence.sh

# Diagnostic de l'infrastructure  
./diagnostic_persistence.sh

# Surveillance continue du flux
./monitor-flow.sh

# Correction des problèmes de données
./fix_data_flow.sh
```

## 🔒 Sécurité

### SNMPv3

L'infrastructure utilise SNMPv3 avec :

- **Authentification** : SHA-1
- **Chiffrement** : AES-128
- **Utilisateur** : `dmeuser`

### Bonnes pratiques

```bash
# Changer les mots de passe par défaut
docker-compose exec elasticsearch bin/elasticsearch-reset-password -u elastic -i

# Appliquer le hardening
./hardening/hardening.sh elasticsearch
./hardening/hardening.sh kibana

# Audit de sécurité
./scripts/security_audit.sh
```

### Pare-feu

Ports à ouvrir en production :

| Port | Service       | Protocole | Accès           |
| ---- | ------------- | --------- | --------------- |
| 5601 | Kibana        | TCP       | Interface web   |
| 9200 | Elasticsearch | TCP       | API (optionnel) |
| 161  | SNMP          | UDP       | DME uniquement  |

## 🔧 Dépannage

### Problèmes courants

#### 1. Services ne démarrent pas

```bash
# Vérifier les logs
docker-compose logs elasticsearch

# Vérifier l'espace disque
df -h

# Redémarrer proprement
docker-compose down && docker-compose up -d
```

#### 2. Pas de données dans Kibana

```bash
# Vérifier la collecte
docker-compose logs data_collector | grep -i logstash

# Vérifier Logstash
curl http://localhost:9600/_node

# Forcer une collecte
docker-compose restart data_collector
```

#### 3. Erreurs de mémoire Elasticsearch

```bash
# Ajuster la mémoire dans docker-compose.yml
environment:
  - "ES_JAVA_OPTS=-Xms1g -Xmx1g"  # Augmenter si nécessaire
```

### Scripts de diagnostic

```bash
# Diagnostic complet
./diag.sh

# Test du flux de données  
./test-complete-flow.sh

# Redémarrage propre en cas de problème
./clean_restart.sh
```

## 📚 Scripts utiles

| Script                | Description                    | Usage                   |
| --------------------- | ------------------------------ | ----------------------- |
| `test_persistence.sh` | Test complet de persistance    | `./test_persistence.sh` |
| `fix_data_flow.sh`    | Correction flux de données     | `./fix_data_flow.sh`    |
| `recovery_script.sh`  | Récupération dashboards Kibana | `./recovery_script.sh`  |
| `diag.sh`             | Diagnostic complet             | `./diag.sh`             |
| `monitor-flow.sh`     | Surveillance temps réel        | `./monitor-flow.sh`     |

## 🔌 API Reference

### DME Simulator API

```bash
# État du service
GET http://localhost:5000/health

# Toutes les métriques DME  
GET http://localhost:5000/all

# Métrique spécifique par OID
GET http://localhost:5000/oid/{oid}

# Liste des OIDs disponibles
GET http://localhost:5000/oids
```

### Elasticsearch API

```bash
# État du cluster
GET http://localhost:9200/_cluster/health

# Recherche dans les données RCMS
GET http://localhost:9200/rcms-dme-*/_search

# Comptage des documents
GET http://localhost:9200/rcms-dme-*/_count
```

## 📁 Structure du projet

```
RCMS_Test/
├── vm1_dme_simulator/          # Simulateur DME
│   ├── dme_simulator_snmpv3.py
│   ├── Dockerfile
│   └── requirements.txt
├── vm2_data_collector/         # Collecteur de données
│   ├── dme_collector.py
│   ├── Dockerfile
│   └── requirements.txt
├── vm3_elasticsearch/          # Configuration Elasticsearch
│   ├── elasticsearch.yml
│   └── certs/
├── vm4_logstash/              # Configuration Logstash
│   ├── pipeline/dme_pipeline.conf
│   └── config/logstash.yml
├── vm5_kibana/                # Configuration Kibana
│   └── kibana.yml
├── hardening/                 # Scripts de sécurisation
├── scripts/                   # Scripts utiles
├── docs/                      # Documentation
├── data/                      # Données CSV (persistantes)
├── logs/                      # Logs (persistants)
└── docker-compose.yml         # Orchestration
```

## 🚧 Limitations connues

- **Collecte SNMPv3** : Actuellement utilise l'API REST comme fallback
- **Sécurité** : Mots de passe par défaut à changer en production
- **Performance** : Optimisé pour 1000-10000 métriques/jour
- **Sauvegarde** : Pas de sauvegarde automatique Elasticsearch (manuelle)

## 📈 Performances

### Métriques typiques

- **Collecte** : 1 cycle toutes les 3 minutes
- **Latence** : < 5 secondes de la collecte à l'affichage
- **Stockage** : ~1MB par jour de données DME
- **Rétention** : 30 jours par défaut (configurable)

### Optimisations

```bash
# Augmenter la mémoire Elasticsearch
ES_JAVA_OPTS=-Xms2g -Xmx2g

# Réduire l'intervalle de collecte
COLLECTION_INTERVAL=60  # 1 minute

# Optimiser les index
PUT http://localhost:9200/rcms-dme-*/_settings
{
  "index.refresh_interval": "30s"
}
```

## 🤝 Contribution

1. **Fork** le projet
2. **Créer** une branche feature (`git checkout -b feature/AmazingFeature`)
3. **Commit** vos changements (`git commit -m 'Add AmazingFeature'`)
4. **Push** vers la branche (`git push origin feature/AmazingFeature`)
5. **Ouvrir** une Pull Request

### Standards de code

- **Python** : PEP 8
- **Docker** : Multi-stage builds
- **Documentation** : Markdown avec badges
- **Tests** : Scripts de validation inclus

## 📞 Support

- 📧 **Email** : support@rcms-test.com
- 📖 **Documentation** : [Wiki du projet](https://claude.ai/chat/docs/)
- 🐛 **Bugs** : [Issues GitHub](https://claude.ai/chat/issues)
- 💬 **Discussions** : [Forum communautaire](https://claude.ai/chat/discussions)

## 📄 License

Ce projet est sous licence MIT. Voir le fichier [LICENSE](https://claude.ai/chat/LICENSE) pour plus de détails.

------

**Développé avec ❤️ pour la sécurité aérienne**

> 💡 **Astuce** : Consultez le dossier `docs/` pour des guides détaillés et le dossier `scripts/` pour des outils de maintenance avancés.