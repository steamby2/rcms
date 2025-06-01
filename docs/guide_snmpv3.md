# Guide SNMPv3 - RCMS_Test
# Auteur: Arthur

## Table des matières
1. [Introduction à SNMPv3](#introduction-à-snmpv3)
2. [Avantages de SNMPv3](#avantages-de-snmpv3)
3. [Configuration SNMPv3](#configuration-snmpv3)
4. [Utilisation avec le simulateur DME](#utilisation-avec-le-simulateur-dme)
5. [Utilisation avec le collecteur de données](#utilisation-avec-le-collecteur-de-données)
6. [Dépannage](#dépannage)
7. [Bonnes pratiques de sécurité](#bonnes-pratiques-de-sécurité)

## Introduction à SNMPv3

SNMPv3 (Simple Network Management Protocol version 3) est la version la plus récente et la plus sécurisée du protocole SNMP. Contrairement à ses prédécesseurs (SNMPv1 et SNMPv2c), SNMPv3 intègre des mécanismes robustes de sécurité, notamment l'authentification et le chiffrement des données.

Dans le cadre du projet RCMS_Test, SNMPv3 est utilisé pour sécuriser les communications entre le simulateur DME (VM1) et le collecteur de données (VM2), garantissant ainsi l'intégrité, la confidentialité et l'authenticité des données de surveillance DME.

## Avantages de SNMPv3

SNMPv3 offre plusieurs avantages critiques pour la sécurité des infrastructures de monitoring :

1. **Authentification** : Vérifie l'identité des agents et des gestionnaires SNMP, empêchant les accès non autorisés.
2. **Confidentialité** : Chiffre les données échangées, empêchant l'interception et la lecture des informations sensibles.
3. **Intégrité** : Garantit que les données n'ont pas été modifiées pendant leur transmission.
4. **Contrôle d'accès** : Permet de définir des politiques d'accès précises pour différents utilisateurs et groupes.
5. **Protection contre les attaques** : Résiste aux attaques par rejeu, par force brute et par interception.

## Configuration SNMPv3

### Modèle de sécurité USM (User-based Security Model)

SNMPv3 utilise le modèle de sécurité basé sur l'utilisateur (USM) qui nécessite la configuration des éléments suivants :

1. **Utilisateurs** : Identifiants uniques pour l'authentification.
2. **Protocoles d'authentification** : Algorithmes pour vérifier l'identité (MD5, SHA).
3. **Mots de passe d'authentification** : Secrets partagés pour l'authentification.
4. **Protocoles de confidentialité** : Algorithmes pour le chiffrement des données (DES, AES).
5. **Mots de passe de confidentialité** : Secrets partagés pour le chiffrement.

### Niveaux de sécurité

SNMPv3 définit trois niveaux de sécurité :

1. **noAuthNoPriv** : Pas d'authentification, pas de chiffrement (déconseillé).
2. **authNoPriv** : Authentification, pas de chiffrement.
3. **authPriv** : Authentification et chiffrement (recommandé et utilisé dans RCMS_Test).

### Configuration dans RCMS_Test

Dans notre infrastructure, les paramètres SNMPv3 sont configurés via des variables d'environnement dans le fichier `docker-compose.yml` :

```yaml
environment:
  - SNMP_USER=dmeuser
  - SNMP_AUTH_PROTOCOL=SHA
  - SNMP_AUTH_PASSWORD=authpassword
  - SNMP_PRIV_PROTOCOL=AES
  - SNMP_PRIV_PASSWORD=privpassword
```

**Important** : En production, remplacez les mots de passe par défaut par des valeurs fortes et uniques.

## Utilisation avec le simulateur DME

Le simulateur DME (VM1) est configuré comme un agent SNMPv3 qui expose les OIDs DME via le protocole SNMPv3. La configuration est effectuée dans le script `dme_simulator_snmpv3.py`.

### Fonctionnement

1. Le simulateur crée un moteur SNMP et configure le transport UDP sur le port 161.
2. Il enregistre un utilisateur SNMPv3 avec les paramètres d'authentification et de chiffrement.
3. Il configure les droits d'accès pour cet utilisateur.
4. Il enregistre les OIDs DME dans la MIB (Management Information Base).
5. Il met à jour périodiquement les valeurs des OIDs avec des données simulées.

### Vérification du fonctionnement

Pour vérifier que l'agent SNMPv3 fonctionne correctement, vous pouvez utiliser la commande `snmpwalk` depuis un autre conteneur :

```bash
snmpwalk -v3 -l authPriv -u dmeuser -a SHA -A authpassword -x AES -X privpassword dme_simulator:161 1.3.6.1.4.1.32275.2.1.2.2
```

## Utilisation avec le collecteur de données

Le collecteur de données (VM2) est configuré comme un gestionnaire SNMPv3 qui interroge périodiquement le simulateur DME. La configuration est effectuée dans le script `dme_collector_snmpv3.py`.

### Fonctionnement

1. Le collecteur crée une session SNMPv3 avec les paramètres d'authentification et de chiffrement.
2. Il interroge périodiquement les OIDs DME via des requêtes SNMPv3 GET.
3. Il traite les réponses et formate les données pour l'enregistrement et l'envoi à Logstash.
4. En cas d'échec des requêtes SNMPv3, il peut utiliser curl comme méthode alternative (si configuré).

### Méthodes de collecte

Le collecteur prend en charge deux méthodes de collecte :

1. **SNMPv3 natif** : Utilise la bibliothèque pysnmp pour les requêtes SNMPv3.
2. **Curl avec authentification** : Méthode alternative utilisant curl pour interroger l'API REST du simulateur.

## Dépannage

### Problèmes courants et solutions

#### Erreurs d'authentification SNMPv3

```
Erreur SNMP: Authentication failure (incorrect password, community or key)
```

**Solution** : Vérifiez que les paramètres d'authentification (utilisateur, protocole, mot de passe) sont identiques entre le simulateur et le collecteur.

#### Erreurs de chiffrement SNMPv3

```
Erreur SNMP: Decryption error
```

**Solution** : Vérifiez que les paramètres de chiffrement (protocole, mot de passe) sont identiques entre le simulateur et le collecteur.

#### Timeout des requêtes SNMPv3

```
Erreur SNMP: No SNMP response received before timeout
```

**Solutions** :
- Vérifiez que le simulateur est en cours d'exécution et accessible sur le réseau.
- Augmentez la valeur du timeout dans la configuration du collecteur.
- Vérifiez que le port UDP 161 est ouvert dans le pare-feu.

## Bonnes pratiques de sécurité

Pour garantir la sécurité optimale de votre infrastructure SNMPv3, suivez ces recommandations :

1. **Utilisez toujours le niveau de sécurité authPriv** pour garantir à la fois l'authentification et le chiffrement.
2. **Préférez SHA à MD5** pour l'authentification, car SHA est cryptographiquement plus robuste.
3. **Préférez AES à DES** pour le chiffrement, car AES offre une meilleure sécurité.
4. **Utilisez des mots de passe forts et uniques** pour l'authentification et le chiffrement.
5. **Changez régulièrement les mots de passe** pour limiter les risques en cas de compromission.
6. **Limitez l'accès au port SNMP (161/UDP)** aux seules adresses IP nécessaires.
7. **Surveillez les journaux d'accès SNMP** pour détecter les tentatives d'accès non autorisées.
8. **Mettez à jour régulièrement les bibliothèques SNMP** pour corriger les vulnérabilités connues.

En suivant ces recommandations, vous garantirez la sécurité des communications entre le simulateur DME et le collecteur de données, contribuant ainsi à la sécurité globale de l'infrastructure de monitoring.
