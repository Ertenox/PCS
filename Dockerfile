# Étape 1 : Utilisation de l'image de base OpenJDK
FROM openjdk:17-jdk-alpine

# Étape 2 : Définition du répertoire de travail
WORKDIR /app

# Étape 3 : Copie du fichier JAR pré-compilé
COPY ./Tuto-Web-service/target/tuto-0.0.1-SNAPSHOT.jar /app/tuto-0.0.1-SNAPSHOT.jar

# Étape 4 : Définition de la commande d'exécution
CMD ["java", "-jar", "tuto-0.0.1-SNAPSHOT.jar"]
