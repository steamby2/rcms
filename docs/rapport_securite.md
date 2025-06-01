# Rapport de Sécurité - Infrastructure RCMS_Test
# Auteur: Arthur

## Table des matières
1. [Introduction](#introduction)
2. [Évaluation des risques](#évaluation-des-risques)
3. [Mesures de sécurité implémentées](#mesures-de-sécurité-implémentées)
4. [Recommandations](#recommandations)
5. [Conclusion](#conclusion)

## Introduction

Ce rapport présente l'analyse de sécurité de l'infrastructure de monitoring RCMS_Test pour la surveillance des balises DME (Distance Measuring Equipment). L'objectif est d'évaluer les risques potentiels et de documenter les mesures de sécurité mises en place pour garantir l'intégrité, la disponibilité et la confidentialité des données DME.

## Évaluation des risques

### Risques identifiés

| Risque | Probabilité | Impact | Niveau de risque |
|--------|-------------|--------|------------------|
| Accès non autorisé aux données DME | Moyenne | Élevé | Élevé |
| Interruption du service de monitoring | Faible | Élevé | Moyen |
| Manipulation des données collectées | Moyenne | Élevé | Élevé |
| Attaque par déni de service | Moyenne | Moyen | Moyen |
| Fuite de données sensibles | Faible | Élevé | Moyen |
| Compromission des conteneurs | Faible | Élevé | Moyen |
| Exploitation de vulnérabilités logicielles | Moyenne | Élevé | Élevé |

### Vecteurs d'attaque potentiels

1. **Exploitation des interfaces réseau exposées**
   - API REST du simulateur DME
   - Interface web Kibana
   - API Elasticsearch

2. **Attaques sur les communications inter-conteneurs**
   - Interception des données entre le collecteur et Logstash
   - Manipulation des données transmises à Elasticsearch

3. **Compromission des conteneurs Docker**
   - Exploitation de vulnérabilités dans les images de base
   - Escalade de privilèges dans les conteneurs

4. **Attaques sur l'hôte Docker**
   - Accès non autorisé au système hôte
   - Exploitation des volumes partagés

## Mesures de sécurité implémentées

### Sécurisation des conteneurs

1. **Isolation réseau**
   - Réseau Docker dédié avec sous-réseau isolé
   - Communication inter-conteneurs limitée aux services nécessaires
   - Exposition minimale des ports vers l'extérieur

2. **Durcissement des conteneurs**
   - Utilisation d'images de base minimalistes (Python slim, Elastic officielles)
   - Exécution des services avec des utilisateurs non privilégiés
   - Limitation des capacités des conteneurs

3. **Gestion des secrets**
   - Utilisation de variables d'environnement pour les informations sensibles
   - Pas de secrets codés en dur dans les images

### Sécurisation des communications

1. **Chiffrement TLS/SSL**
   - Certificats SSL pour toutes les communications inter-services
   - Configuration HTTPS pour Kibana et Elasticsearch
   - Validation des certificats entre les composants

2. **Authentification**
   - Authentification requise pour accéder à Elasticsearch et Kibana
   - Limitation des tentatives de connexion avec Fail2ban

### Durcissement des systèmes

1. **Pare-feu**
   - Configuration UFW restrictive pour chaque service
   - Règles de filtrage par défaut en mode "deny all"
   - Ouverture uniquement des ports nécessaires

2. **Mises à jour automatiques**
   - Configuration des mises à jour de sécurité automatiques
   - Surveillance des CVE pour les composants utilisés

3. **Audit et journalisation**
   - Journalisation complète des activités système
   - Centralisation des logs dans Elasticsearch
   - Alertes sur les événements de sécurité

### Surveillance et détection

1. **Détection d'anomalies**
   - Analyse des logs en temps réel avec Logstash
   - Détection des comportements anormaux dans les métriques DME
   - Alertes sur les écarts significatifs

2. **Surveillance de l'intégrité**
   - Vérification de l'intégrité des fichiers critiques
   - Surveillance des modifications de configuration

## Recommandations

### Améliorations à court terme

1. **Renforcement de l'authentification**
   - Mise en place d'une authentification à deux facteurs pour Kibana
   - Rotation régulière des mots de passe et des clés

2. **Segmentation réseau avancée**
   - Mise en place de règles de filtrage plus granulaires entre les services
   - Utilisation de réseaux Docker distincts pour chaque couche de l'application

3. **Chiffrement des données au repos**
   - Chiffrement des volumes de données Elasticsearch
   - Chiffrement des fichiers CSV générés par le collecteur

### Améliorations à moyen terme

1. **Mise en place d'un WAF**
   - Protection des API exposées avec un pare-feu applicatif
   - Filtrage des requêtes malveillantes

2. **Surveillance avancée de la sécurité**
   - Intégration d'outils de détection d'intrusion
   - Analyse comportementale des accès et des requêtes

3. **Tests de pénétration réguliers**
   - Évaluation périodique de la sécurité de l'infrastructure
   - Correction des vulnérabilités identifiées

## Conclusion

L'infrastructure RCMS_Test a été conçue avec un focus important sur la sécurité, en appliquant les principes de défense en profondeur. Les mesures de sécurité implémentées couvrent les aspects d'authentification, de chiffrement, d'isolation et de surveillance, offrant une protection robuste contre les menaces courantes.

Cependant, la sécurité est un processus continu qui nécessite une vigilance constante. Les recommandations proposées permettront de renforcer davantage la posture de sécurité de l'infrastructure et de s'adapter à l'évolution des menaces.

L'application rigoureuse des procédures de hardening, combinée à une surveillance active et à des mises à jour régulières, permettra de maintenir un niveau de sécurité élevé pour la surveillance des balises DME, contribuant ainsi à la sécurité aérienne globale.
