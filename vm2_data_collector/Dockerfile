# Dockerfile pour le collecteur de données DME
# Auteur: Arthur

FROM python:3.9-slim

WORKDIR /app

# Installation des dépendances système
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copie des fichiers de l'application
COPY dme_collector.py /app/
COPY requirements.txt /app/

# Installation des dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Création des répertoires pour les données et les logs
RUN mkdir -p /app/data /app/logs

# Commande de démarrage
CMD ["python", "dme_collector.py"]
