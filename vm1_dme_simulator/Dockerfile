# Dockerfile pour l'agent SNMPv3 DME
# Auteur: Arthur

FROM python:3.9-slim

WORKDIR /app

# Pas besoin de snmpd pour la simulation
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Copie des fichiers
COPY dme_simulator_snmpv3.py /app/
COPY requirements.txt /app/

RUN pip install --no-cache-dir -r requirements.txt

# Création des répertoires
RUN mkdir -p /app/logs

# Exposition du port SNMP
EXPOSE 161/udp

# Commande de démarrage
CMD ["python", "dme_simulator_snmpv3.py"]
