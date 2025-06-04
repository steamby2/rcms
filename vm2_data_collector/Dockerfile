# Dockerfile pour le collecteur SNMPv3 DME
# Auteur: Arthur

FROM python:3.9-slim

WORKDIR /app

# Copie des fichiers
COPY dme_collector_snmpv3.py /app/
COPY requirements.txt /app/

# Installation des dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Création des répertoires
RUN mkdir -p /app/data /app/logs

# Commande de démarrage
CMD ["python", "dme_collector_snmpv3.py"]
