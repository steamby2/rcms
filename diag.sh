#!/bin/bash
# Script de diagnostic complet pour RCMS_Test
# Analyse tous les composants et identifie les problèmes
# Auteur: Arthur

set -e

echo "=== DIAGNOSTIC COMPLET RCMS_TEST ==="
echo "Date: $(date)"
echo ""

# Couleurs pour l'affichage
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Fonction pour afficher avec couleur
print_status() {
    local status=$1
    local message=$2
    case $status in
        "OK") echo -e "${GREEN}✓ $message${NC}" ;;
        "WARNING") echo -e "${YELLOW}⚠ $message${NC}" ;;
        "ERROR") echo -e "${RED}✗ $message${NC}" ;;
        "INFO") echo -e "${BLUE}ℹ $message${NC}" ;;
    esac
}

# 1. VERIFICATION DE L'ETAT DES SERVICES
echo "1. ÉTAT DES SERVICES DOCKER"
echo "=================================="
services_status=$(docker-compose ps --format table 2>/dev/null || echo "ERROR")

if [ "$services_status" = "ERROR" ]; then
    print_status "ERROR" "Impossible d'obtenir l'état des services"
    exit 1
else
    docker-compose ps
    echo ""
fi

# Vérifier si tous les services sont UP
services_down=$(docker-compose ps | grep -v "Up" | grep -c "Exit\|Restarting" || echo "0")
if [ "$services_down" -gt 0 ]; then
    print_status "ERROR" "$services_down service(s) ne fonctionne(nt) pas correctement"
else
    print_status "OK" "Tous les services Docker sont opérationnels"
fi

echo ""

# 2. TEST DE CONNECTIVITE DES APIs
echo "2. TEST DE CONNECTIVITÉ DES APIs"
echo "================================="

# Test DME Simulator
if curl -s -f http://localhost:5000/health >/dev/null 2>&1; then
    print_status "OK" "DME Simulator API accessible"
    
    # Test de récupération des données
    dme_data=$(curl -s http://localhost:5000/all 2>/dev/null)
    if echo "$dme_data" | grep -q "data"; then
        print_status "OK" "DME Simulator retourne des données"
        
        # Compter le nombre de métriques
        metrics_count=$(echo "$dme_data" | jq '.data | length' 2>/dev/null || echo "0")
        print_status "INFO" "Nombre de métriques DME: $metrics_count"
    else
        print_status "ERROR" "DME Simulator ne retourne pas de données valides"
    fi
else
    print_status "ERROR" "DME Simulator API non accessible"
fi

# Test Elasticsearch
if curl -s -f http://localhost:9200/_cluster/health >/dev/null 2>&1; then
    print_status "OK" "Elasticsearch API accessible"
    
    # Vérifier le statut du cluster
    cluster_status=$(curl -s http://localhost:9200/_cluster/health | jq -r '.status' 2>/dev/null || echo "unknown")
    case $cluster_status in
        "green") print_status "OK" "Cluster Elasticsearch: GREEN" ;;
        "yellow") print_status "WARNING" "Cluster Elasticsearch: YELLOW" ;;
        "red") print_status "ERROR" "Cluster Elasticsearch: RED" ;;
        *) print_status "ERROR" "Statut cluster inconnu: $cluster_status" ;;
    esac
    
    # Vérifier les indices
    indices_count=$(curl -s "http://localhost:9200/_cat/indices" | wc -l 2>/dev/null || echo "0")
    print_status "INFO" "Nombre d'indices Elasticsearch: $indices_count"
    
    # Vérifier spécifiquement les indices RCMS
    rcms_indices=$(curl -s "http://localhost:9200/_cat/indices/rcms-dme-*" 2>/dev/null | wc -l || echo "0")
    if [ "$rcms_indices" -gt 0 ]; then
        print_status "OK" "Indices RCMS trouvés: $rcms_indices"
    else
        print_status "WARNING" "Aucun indice RCMS trouvé"
    fi
    
    # Compter les documents dans les indices RCMS
    rcms_docs=$(curl -s "http://localhost:9200/rcms-dme-*/_count" 2>/dev/null | jq '.count' 2>/dev/null || echo "0")
    print_status "INFO" "Documents RCMS dans Elasticsearch: $rcms_docs"
    
else
    print_status "ERROR" "Elasticsearch API non accessible"
fi

# Test Kibana
if curl -s -f http://localhost:5601/api/status >/dev/null 2>&1; then
    print_status "OK" "Kibana API accessible"
else
    print_status "ERROR" "Kibana API non accessible"
fi

# Test Logstash
if curl -s -f http://localhost:9600/_node >/dev/null 2>&1; then
    print_status "OK" "Logstash API accessible"
else
    print_status "WARNING" "Logstash API non accessible (vérifier la configuration)"
fi

echo ""

# 3. VERIFICATION DES DONNEES LOCALES
echo "3. DONNÉES LOCALES (CSV)"
echo "========================"

csv_file="./data/dme_data.csv"
if [ -f "$csv_file" ]; then
    print_status "OK" "Fichier CSV trouvé: $csv_file"
    
    # Compter les lignes
    line_count=$(wc -l < "$csv_file" 2>/dev/null || echo "0")
    data_lines=$((line_count - 1))  # Exclure l'en-tête
    print_status "INFO" "Lignes de données CSV: $data_lines"
    
    # Vérifier la date de dernière modification
    if command -v stat >/dev/null 2>&1; then
        last_modified=$(stat -c %Y "$csv_file" 2>/dev/null || date +%s)
        current_time=$(date +%s)
        diff_seconds=$((current_time - last_modified))
        
        if [ $diff_seconds -lt 300 ]; then  # Moins de 5 minutes
            print_status "OK" "Fichier CSV récemment mis à jour (il y a ${diff_seconds}s)"
        else
            print_status "WARNING" "Fichier CSV pas mis à jour récemment (il y a ${diff_seconds}s)"
        fi
    fi
    
    # Afficher les dernières lignes
    echo ""
    echo "Dernières entrées CSV:"
    tail -n 3 "$csv_file" 2>/dev/null || echo "Impossible de lire le fichier"
    
else
    print_status "ERROR" "Fichier CSV non trouvé: $csv_file"
fi

echo ""

# 4. ANALYSE DES LOGS
echo "4. ANALYSE DES LOGS"
echo "==================="

# Logs du simulateur DME
echo "--- Simulateur DME ---"
dme_errors=$(docker-compose logs dme_simulator 2>/dev/null | grep -i error | wc -l || echo "0")
if [ "$dme_errors" -eq 0 ]; then
    print_status "OK" "Aucune erreur dans les logs DME Simulator"
else
    print_status "WARNING" "$dme_errors erreur(s) dans les logs DME Simulator"
fi

# Logs du collecteur
echo "--- Collecteur de données ---"
collector_errors=$(docker-compose logs data_collector 2>/dev/null | grep -i error | wc -l || echo "0")
if [ "$collector_errors" -eq 0 ]; then
    print_status "OK" "Aucune erreur dans les logs du collecteur"
else
    print_status "WARNING" "$collector_errors erreur(s) dans les logs du collecteur"
fi

# Vérifier si le collecteur envoie à Logstash
logstash_sends=$(docker-compose logs data_collector 2>/dev/null | grep -i "logstash" | wc -l || echo "0")
if [ "$logstash_sends" -gt 0 ]; then
    print_status "INFO" "Le collecteur tente d'envoyer à Logstash ($logstash_sends tentatives)"
else
    print_status "WARNING" "Aucune tentative d'envoi vers Logstash détectée"
fi

# Logs Elasticsearch
echo "--- Elasticsearch ---"
es_errors=$(docker-compose logs elasticsearch 2>/dev/null | grep -i "error\|exception" | wc -l || echo "0")
if [ "$es_errors" -eq 0 ]; then
    print_status "OK" "Aucune erreur dans les logs Elasticsearch"
else
    print_status "WARNING" "$es_errors erreur(s) dans les logs Elasticsearch"
fi

# Logs Logstash
echo "--- Logstash ---"
logstash_errors=$(docker-compose logs logstash 2>/dev/null | grep -i "error\|exception\|failed" | wc -l || echo "0")
if [ "$logstash_errors" -eq 0 ]; then
    print_status "OK" "Aucune erreur dans les logs Logstash"
else
    print_status "ERROR" "$logstash_errors erreur(s) dans les logs Logstash"
    
    # Afficher les dernières erreurs Logstash
    echo ""
    echo "Dernières erreurs Logstash:"
    docker-compose logs logstash 2>/dev/null | grep -i "error\|exception\|failed" | tail -n 5 || echo "Aucune erreur détaillée"
fi

# Logs Kibana
echo "--- Kibana ---"
kibana_errors=$(docker-compose logs kibana 2>/dev/null | grep -i "error\|exception" | wc -l || echo "0")
if [ "$kibana_errors" -eq 0 ]; then
    print_status "OK" "Aucune erreur dans les logs Kibana"
else
    print_status "WARNING" "$kibana_errors erreur(s) dans les logs Kibana"
fi

echo ""

# 5. VERIFICATION DE LA CONFIGURATION
echo "5. CONFIGURATION"
echo "================"

# Vérifier la config du collecteur
if docker-compose exec data_collector env | grep -q "LOGSTASH_ENABLED=true"; then
    print_status "OK" "Collecteur configuré pour envoyer à Logstash"
else
    print_status "WARNING" "Collecteur PAS configuré pour envoyer à Logstash"
    echo "    → Variable LOGSTASH_ENABLED n'est pas à 'true'"
fi

# Vérifier les variables d'environnement
echo ""
echo "Variables d'environnement du collecteur:"
docker-compose exec data_collector env | grep -E "(LOGSTASH|DME_SIMULATOR)" 2>/dev/null || echo "Impossible de récupérer les variables"

echo ""

# 6. RECOMMANDATIONS
echo "6. DIAGNOSTIC ET RECOMMANDATIONS"
echo "================================="

# Analyser les problèmes détectés
problems_found=0

# Problème 1: Pas de données dans Elasticsearch
if [ "$rcms_docs" -eq 0 ]; then
    problems_found=$((problems_found + 1))
    print_status "ERROR" "PROBLÈME 1: Aucune donnée dans Elasticsearch"
    echo "   → Les données ne remontent pas du collecteur vers Elasticsearch"
    echo "   → Vérifier la configuration Logstash et la connectivité"
fi

# Problème 2: Logstash désactivé
if ! docker-compose exec data_collector env | grep -q "LOGSTASH_ENABLED=true" 2>/dev/null; then
    problems_found=$((problems_found + 1))
    print_status "ERROR" "PROBLÈME 2: Logstash désactivé dans le collecteur"
    echo "   → Le collecteur ne transmet pas les données à Logstash"
    echo "   → LOGSTASH_ENABLED doit être à 'true'"
fi

# Problème 3: Erreurs Logstash
if [ "$logstash_errors" -gt 0 ]; then
    problems_found=$((problems_found + 1))
    print_status "ERROR" "PROBLÈME 3: Erreurs dans Logstash"
    echo "   → $logstash_errors erreurs détectées dans Logstash"
    echo "   → Vérifier la configuration du pipeline"
fi

if [ $problems_found -eq 0 ]; then
    print_status "OK" "Aucun problème majeur détecté"
    echo "   → L'infrastructure semble fonctionnelle"
    echo "   → Les données peuvent prendre quelques minutes à apparaître"
else
    echo ""
    print_status "INFO" "ACTIONS RECOMMANDÉES:"
    echo "   1. Activer Logstash dans le collecteur"
    echo "   2. Corriger la configuration Logstash" 
    echo "   3. Redémarrer les services avec les corrections"
    echo "   4. Attendre 5-10 minutes pour voir les données"
fi

echo ""
echo "=== FIN DU DIAGNOSTIC ==="
echo "Fichier de log généré: diagnostic_$(date +%Y%m%d_%H%M%S).log"