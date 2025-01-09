import git
import json
import time
import os
import subprocess
import requests
import time
from requests.auth import HTTPBasicAuth

def run_maven():
    """Compile le projet Maven."""
    print("Compilation Maven en cours...")

    result = subprocess.run(["mvn clean install"], capture_output=True, text=True, shell=True)
    if result.returncode == 0:
        print("Maven : Compilation réussi !")
    else:
        print("Maven : Erreur de compilation .")
        print(result.stdout)
        print(result.stderr)
        exit(result.returncode)

def run_docker():
    """Lance le conteneur Docker."""
    id = os.popen("date +%Y%m%d").read().strip()  
    print("Création de l'image docker...")
    result = subprocess.run(
        ["docker", "images"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        lines = result.stdout.strip().split('\n')
        if len(lines) > 1:
            second_line = lines[1]
        else:
            print("No docker images found.")
    else:
        print("Error running docker images command:", result.stderr)
    try:    
        oldimagename = second_line.split()[0]
        oldcontainername = oldimagename.split('_')[0]+"_container_"+oldimagename.split('_')[1]
        subprocess.run(
            ["docker", "stop", oldcontainername],
            capture_output=True,
            text=True,
            shell=False
        )
        subprocess.run(
            ["docker", "container", "rm", oldcontainername],
            capture_output=True,
            text=True,
            shell=False
        )
        subprocess.run(
            ["docker", "tag", oldimagename, "app_old"],
            capture_output=True,
            text=True,
            shell=False
        )
        subprocess.run(
            ["docker", "rmi", oldimagename],
            capture_output=True,
            text=True,
            shell=False
        )
    except:
        print("No old image found")    
    result = subprocess.run(
        ["docker", "build", "-t", f"app_{id}", "."],
        capture_output=True,
        text=True,
        shell=False  
    )
    if result.returncode == 0:
        print("Docker : Image créée avec succès !")

        # Lancement du conteneur Docker
        print("Lancement du conteneur...")
        run_result = subprocess.run(
        ["docker", "run", "-p", "8080:8080","-d","--name", f"app_container_{id}",f"app_{id}"],
            capture_output=True,
            text=True,
            shell=False  
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
        time.sleep(30)
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
        formatted_text = response.text.replace(",", ",\n")
        formatted_json_lines = formatted_text.splitlines()
        filtered_json_lines = [line for line in formatted_json_lines if not line.strip().startswith('"message"')]

        # Rejoindre les lignes filtrées
        filtered_json = "\n".join(filtered_json_lines)
        data = json.loads(filtered_json.strip())

        # Vérifier la gravité des issues
        for issue in data.get("issues", []):
            severity = issue.get('severity')
            resolution = issue.get('resolution')
            if severity in ["BLOCKER", "HIGH"] and resolution != "FIXED":
                return False
        return True
    else:
        print("Erreur lors de la récupération des issues.")
        print("Code de réponse:", response.status_code)

if __name__ == "__main__":
    os.chdir("/home/cicd/PCS")
    if os.path.exists("/home/cicd/PCS/Tuto-Web-service"):
        os.system("rm -rf /home/cicd/PCS/Tuto-Web-service")
        print("Suppression du dossier existant.")
    print("Clonage du projet...")
    git.Git().clone("https://github.com/Ertenox/Tuto-Web-service.git")
    os.chdir("/home/cicd/PCS/Tuto-Web-service")
    run_maven()
    if sonar_check():
        os.chdir("/home/cicd/PCS")
        run_docker()



