# Dockerfile pour agent SNMP DME fonctionnel
# Auteur: Arthur

FROM python:3.9-slim

WORKDIR /app

# Pas besoin de snmpd pour la simulation
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copie des fichiers
COPY working_snmp_agent.py /app/
COPY requirements.txt /app/

# Installation des dépendances Python (aucune nécessaire)
RUN pip install --no-cache-dir -r requirements.txt

# Création des répertoires
RUN mkdir -p /app/logs

# Exposition du port SNMP
EXPOSE 161/udp

# Commande de démarrage
CMD ["python", "working_snmp_agent.py"]
