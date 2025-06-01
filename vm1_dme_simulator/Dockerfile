# Dockerfile pour le simulateur DME
# Auteur: Arthur

FROM python:3.9-slim

WORKDIR /app

# Installation des dépendances système
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copie des fichiers de l'application
COPY dme_simulator.py /app/
COPY requirements.txt /app/

# Installation des dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Création du répertoire pour les logs
RUN mkdir -p /app/logs

# Exposition du port
EXPOSE 5000

# Commande de démarrage
CMD ["python", "dme_simulator.py"]
