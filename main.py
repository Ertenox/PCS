import git
import os
import subprocess
import requests
from requests.auth import HTTPBasicAuth

def run_maven():
    """Compile le projet Maven."""
    print("Compilation Maven en cours...")
    result = subprocess.run(["mvn", "clean", "install"], capture_output=True, text=True, shell=True)
    if result.returncode == 0:
        print("Maven : Compilation réussi !")
    else:
        print("Maven : Erreur de compilation .")
        print(result.stdout)
        print(result.stderr)
        exit(result.returncode)

import subprocess

def run_docker():
    """Lance le conteneur Docker."""
    print("Création de l'image docker...")
    result = subprocess.run(["docker", "build", "-t", "app", "."], capture_output=True, text=True, shell=True)
    if result.returncode == 0:
        print("Docker : Image créée avec succès !")

        # Lancement du conteneur Docker
        print("Lancement du conteneur...")
        run_result = subprocess.run(
            ["docker", "run", "-d", "--name", "app_container", "app"],
            capture_output=True,
            text=True,
            shell=True
        )
        if run_result.returncode == 0:
            print("Docker : Conteneur lancé avec succès !")
            print("ID du conteneur :", run_result.stdout.strip())
        else:
            print("Docker : Erreur lors du lancement du conteneur.")
            print(run_result.stdout)
            print(run_result.stderr)
            exit(run_result.returncode)
    else:
        print("Docker : Erreur lors de la création de l'image.")
        print(result.stdout)
        print(result.stderr)
        exit(result.returncode)

def sonar_check():
    """Lance l'analyse du code via SonarQube."""
    print("Analyse du code en cours...")

    # Définition de la commande sonar-scanner
    sonar_command = [
        "/usr/local/sonar-scanner-6.2.1.4610-linux-x64/bin/sonar-scanner",
        "-Dsonar.projectKey=PCS",
        "-Dsonar.sources=src/main/java",
        "-Dsonar.java.binaries=target/classes",
        "-Dsonar.host.url=http://localhost:9000",
        "-Dsonar.token=sqp_a7c637668c75fa0d80d8b21c4f15cc0adbcd27c1"
    ]

    # Exécution de la commande et capture de la sortie
    result = subprocess.run(sonar_command, capture_output=True, text=True)
    print(result)
    # Affichage du résultat
    if result.returncode == 0:
        print("Analyse SonarQube réussie !")
        print("Sortie de l'analyse :")
        print(result.stdout)
        # Une fois l'analyse terminée, interroger les issues sur SonarQube
        status = get_sonar_issues()
        if status:
            print("Aucun problème de criticité HIGH ou BLOCKER n'a été détécté")
            return status
        else:
            print("Un problème de criticité HIGH ou BLOCKER a été détécté. Le déploiement du code ne peut s'effectuer... Pour plus se rendre sur SonarQube.")
            return status
    else:
        print("Erreur lors de l'analyse SonarQube.")
        print("Sortie d'erreur :")
        print(result.stderr)

def get_sonar_issues():
    """Récupère les issues (bugs, vulnérabilités, smells) du projet via l'API SonarQube."""
    # Authentification avec le token SonarQube
    auth = HTTPBasicAuth('squ_c8f026041b1b34017a4f2a568c9ac4c3a5aa5859', '')  # Le token en guise de mot de passe

    # URL de l'API pour obtenir les issues
    url = "http://localhost:9000/api/issues/search"
    params = {
        'componentKeys': 'PCS',  # Identifiant du projet
        'types': 'BUG,VULNERABILITY,CODE_SMELL',  # Types d'issues à récupérer
    }

    # Envoi de la requête HTTP GET
    response = requests.get(url, auth=auth, params=params)

    if response.status_code == 200:
        print("Problèmes récupérés avec succès :")
        if '"severity":"BLOCKER"' in response.text or '"severity":"HIGH"' in response.text:
           return False
        return True
    else:
        print("Erreur lors de la récupération des issues.")
        print("Code de réponse:", response.status_code)

if __name__ == "__main__":
    #shutil.rmtree("Tuto-Web-service", ignore_errors=True)
    git.Git().clone("https://github.com/DavidIMT/Tuto-Web-service.git")
    os.chdir("Tuto-Web-service")
    run_maven()
    if sonar_check():
        os.chdir("")
        run_docker()
        sonar_check()



