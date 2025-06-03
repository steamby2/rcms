# Dockerfile pour collecteur DME simplifié
# Auteur: Arthur

FROM python:3.9-slim

WORKDIR /app

# Copie des fichiers
COPY simple_collector.py /app/
COPY requirements.txt /app/

# Installation des dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Création des répertoires
RUN mkdir -p /app/data /app/logs

# Commande de démarrage
CMD ["python", "simple_collector.py"]
