import git
import json
import time
import os
import subprocess
import requests
import time
from requests.auth import HTTPBasicAuth
import test_livre_api
import rollback

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

def rollback_docker():
    """Arrête le conteneur Docker."""
    print("Arrêt du conteneur Docker...")

    # Récupérer l'ID du conteneur Docker
    result = subprocess.run(
        ["docker", "ps", "-q", "-l"],
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        container_id = result.stdout.strip()
        if container_id:
            # Arrêter le conteneur Docker
            stop_result = subprocess.run(
                ["docker", "stop", container_id],
                capture_output=True,
                text=True
            )
            if stop_result.returncode == 0:
                print("Conteneur Docker arrêté avec succès.")
                print("Suppression du conteneur Docker...")
                # Supprimer le conteneur Docker
                rm_result = subprocess.run(
                    ["docker", "rm", container_id],
                    capture_output=True,
                    text=True
                )
                if rm_result.returncode == 0:
                    print("Conteneur Docker supprimé avec succès.")
                else:
                    print("Erreur lors de la suppression du conteneur Docker.")
                    print(rm_result.stdout)
                    print(rm_result.stderr)
                    exit(rm_result.returncode)
                # Lancement du conteneur Docker
                print("Lancement de l'ancien conteneur...")
                run_result = subprocess.run(
                ["docker", "run", "-p", "8080:8080","-d","--name", f"app_container_rollback",f"app_old"],
                    capture_output=True,
                    text=True,
                    shell=False  
                )
                if run_result.returncode == 0:
                    print("Docker : Rollback effectué avec succcès !")
                    print("ID du conteneur :", run_result.stdout.strip())
                else:
                    print("Docker : Erreur lors du lancement du conteneur.")
                    print(run_result.stdout)
                    print(run_result.stderr)
                    exit(run_result.returncode)
            else:
                print("Erreur lors de l'arrêt du conteneur Docker.")
                print(stop_result.stdout)
                print(stop_result.stderr)
                exit(stop_result.returncode)
        else:
            print("Aucun conteneur Docker n'est en cours d'exécution.")
    else:
        print("Erreur lors de la récupération de l'ID du conteneur Docker.")
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
        "-Dsonar.token=sqp_a1d4a682b8407e422bf5ea189a5b0034a826226d"
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
    auth = HTTPBasicAuth('squ_3b7f0dd9512aeb9661715e86561a2bae5f27037d', '')  # Le token en guise de mot de passe

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

def test_penetration():
    try:
        # Start the scan
        scan_url = "http://localhost:8000/JSON/ascan/action/scan/?url=http://127.0.0.1:8080&apikey="
        requests.get(scan_url)
        print("Début du scan...")
        
        # Wait for scan completion
        while True:
            response_status = requests.get("http://localhost:8000/JSON/ascan/view/status/").json()
            status = response_status.get('status')
            if status == '100':  # Scan complete
                break
            print(f"Scan de sécurité en cours")
            time.sleep(2)

        print("Scan terminé")
        
        # Fetch the scan results
        report_url = "http://localhost:8000/OTHER/core/other/jsonreport/?apikey="
        scan_json = requests.get(report_url).json()

        # Check for high or medium risks
        sites = scan_json.get("site", [])
        if not sites:
            print("Site non trouvé.")
            return True  # Assume no issues if no sites are scanned

        # Iterate over alerts
        alerts = sites[0].get("alerts", [])
        high = False

        enumRisk = ["High (High)", "High (Medium)", "High (Low)"]

        for alert in alerts:
            risk_desc = alert.get("riskdesc", "")
            for risk in enumRisk:
                if risk in risk_desc:
                    high = True
                    print(f"Risk detected: {risk_desc}")
                    break
            

        if high:
            print("Le test de pénétration a échoué, rollback en cours")
            return False
        else:
            print("Le test de pénétration a réussi, pas de failles majeures détectées")
            return True
            
    except requests.exceptions.RequestException as e:
        print(f"Erreur de connexion avec l'API ZAP: {e}")
        return False
    except KeyError as e:
        print(f"Erreur dans le traitement de la réponse JSON: clé manquante {e}")
        return False
    except Exception as e:
        print(f"Une erreur inattendue est survenue: {e}")
        return False

 
        
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
      
    if test_penetration() or test_livre_api.run_tests() == False:
        rollback.rollback_docker()
    