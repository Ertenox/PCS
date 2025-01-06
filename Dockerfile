FROM python:3.11-slim
# Définition du répertoire de travail 
WORKDIR /app

COPY ./Tuto-Web-service /app
RUN pip install --no-cache-dir -r requirements.txt

# Spécifier la commande par défaut
CMD ["python", "app.py"]
