# Architecture de l'Infrastructure de Monitoring Sécurisée

## Vue d'ensemble

Cette infrastructure de monitoring sécurisée est conçue pour surveiller en temps réel les balises DME (Distance Measuring Equipment) utilisées dans la sécurité aérienne. L'architecture est basée sur une solution virtualisée avec Docker, comprenant 5 machines virtuelles distinctes, chacune avec un rôle spécifique dans le système global.

## Machines Virtuelles et leurs Rôles

### VM1 : Simulateur DME
- **Rôle** : Simuler un système DME réel fournissant des données via des requêtes curl
- **Fonctionnalités** :
  - Exposition d'une API REST simulant les OIDs SNMP d'un DME réel
  - Génération de données simulées pour les paramètres DME (délais, puissance, etc.)
  - Réponse aux requêtes HTTP avec des données au format compatible avec les OIDs spécifiés
- **Technologies** : Python, Flask, Docker
- **Sécurité** : Isolation réseau, limitation des accès, journalisation des requêtes

### VM2 : Collecteur de Données
- **Rôle** : Collecter périodiquement les données du simulateur DME et les formater
- **Fonctionnalités** :
  - Interrogation périodique du simulateur DME via curl
  - Formatage des données collectées avec horodatage
  - Stockage des données dans un format tabulaire
  - Transmission des données vers Logstash pour traitement
- **Technologies** : Python, Docker, Requests
- **Sécurité** : Communications chiffrées, validation des données, gestion des erreurs

### VM3 : Elasticsearch
- **Rôle** : Stockage et indexation des données DME
- **Fonctionnalités** :
  - Stockage persistant des données collectées
  - Indexation pour recherche rapide
  - Gestion des séries temporelles
  - API pour l'interrogation des données
- **Technologies** : Elasticsearch, Docker
- **Sécurité** : Authentification, chiffrement des données au repos, contrôle d'accès

### VM4 : Logstash
- **Rôle** : Traitement et enrichissement des données
- **Fonctionnalités** :
  - Réception des données du collecteur
  - Transformation et normalisation des données
  - Enrichissement avec des métadonnées
  - Transmission vers Elasticsearch
- **Technologies** : Logstash, Docker
- **Sécurité** : Validation des entrées, filtrage des données, chiffrement des communications

### VM5 : Kibana
- **Rôle** : Visualisation et tableau de bord
- **Fonctionnalités** :
  - Interface utilisateur pour visualiser les données DME
  - Tableaux de bord personnalisables
  - Alertes et notifications
  - Rapports et analyses
- **Technologies** : Kibana, Docker
- **Sécurité** : Authentification utilisateur, HTTPS, contrôle d'accès basé sur les rôles

## Flux de Données

1. Le simulateur DME (VM1) génère des données simulées pour les paramètres DME
2. Le collecteur (VM2) interroge périodiquement le simulateur via curl et formate les données
3. Les données formatées sont envoyées à Logstash (VM4) pour traitement
4. Logstash traite, enrichit et normalise les données avant de les transmettre à Elasticsearch (VM3)
5. Elasticsearch indexe et stocke les données pour une recherche et une analyse efficaces
6. Kibana (VM5) fournit une interface utilisateur pour visualiser et analyser les données stockées

## Mesures de Sécurité Globales

- Isolation réseau entre les machines virtuelles
- Chiffrement de toutes les communications inter-VM
- Authentification pour tous les services
- Journalisation complète des activités
- Durcissement (hardening) de chaque système d'exploitation
- Surveillance continue des performances et de la sécurité
- Sauvegarde régulière des données critiques
- Mise à jour automatique des composants logiciels
