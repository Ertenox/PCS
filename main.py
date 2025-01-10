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
import sys

def run_maven():
    """Compile le projet Maven."""
    print("Compilation Maven en cours...", flush=True)

    result = subprocess.run(["mvn clean install"], capture_output=True, text=True, shell=True)
    if result.returncode == 0:
        print("Maven : Compilation réussi !", flush=True)
    else:
        print("Maven : Erreur de compilation .")
        print(result.stdout)
        print(result.stderr)
        exit(result.returncode)

def run_docker():
    id = os.popen("date +%Y%m%d").read().strip()  
    print("Commencement des opérations docker...", flush=True)

    result = subprocess.run(["docker", "ps", "-q", "-l"], capture_output=True, text=True)
    if result.returncode != 0:
        print("Erreur dans la récupération du nom du containeur", result.stderr)
        sys.exit(result.returncode)
    container_id = result.stdout.strip()

    result2 = subprocess.run(["docker", "ps", "-l", "--format", "{{.Image}}"], capture_output=True, text=True)
    if result2.returncode != 0:
        print("Erreur dans la récupération du nom de l'image:", result2.stderr)
        sys.exit(result2.returncode)
    old_image_name = result2.stdout.strip()

    if "app" in old_image_name:
        print(f"Image docker existante trouvée: {old_image_name}", flush=True)

        if container_id:
            stop_result = subprocess.run(["docker", "stop", container_id], capture_output=True, text=True)
            if stop_result.returncode == 0:
                print("Containeur docker arrêté avec succès.", flush=True)
            else:
                print("Erreur dans l'arrêt du containeur précédent: ", stop_result.stderr)
                sys.exit(stop_result.returncode)

            rm_result = subprocess.run(["docker", "rm", container_id], capture_output=True, text=True)
            if rm_result.returncode == 0:
                print("Containeur supprimé avec succès.", flush=True)
            else:
                print("Erreur dans la suppression de:", rm_result.stderr)
                sys.exit(rm_result.returncode)

        tag_result = subprocess.run(["docker", "tag", old_image_name, "app_old"], capture_output=True, text=True)
        if tag_result.returncode == 0:
            print("Image taggé en 'app_old'.", flush=True)
        else:
            print("Erreur en taggant l'image:", tag_result.stderr)
            sys.exit(tag_result.returncode)

        rmi_result = subprocess.run(["docker", "rmi", old_image_name], capture_output=True, text=True)
        if rmi_result.returncode == 0:
            print("Ancienne image supprimée avec succès.", flush=True)
        else:
            print("Erreur dans la suppression de l'ancienne image:", rmi_result.stderr)
            sys.exit(rmi_result.returncode)
    else:
        print("App n'a jamais existé, création d'une image.", flush=True)

    new_image_name = f"app_{id}"
    print(f"Build de l'image: {new_image_name}")
    build_result = subprocess.run(["docker", "build", "-t", new_image_name, "."], capture_output=True, text=True)
    if build_result.returncode == 0:
        print("Image build avec succès.", flush=True)
    else:
        print("Erreur dans le build de l'image:", build_result.stderr)
        sys.exit(build_result.returncode)

    container_name = f"app_container_{id}"
    print(f"Lancement du nouveau conteneur: {container_name}")
    run_result = subprocess.run(
        ["docker", "run", "-p", "8080:8080", "-d", "--name", container_name, new_image_name],
        capture_output=True,
        text=True
    )
    if run_result.returncode == 0:
        print("Conteneur lancé avec succès.", flush=True)
        print("Container ID:", run_result.stdout.strip(), flush=True)
    else:
        print("Erreur dans le lancement:", run_result.stderr)
        sys.exit(run_result.returncode)

def rollback_docker():
    """Arrête le conteneur Docker."""
    print("Arrêt du conteneur Docker...", flush=True)

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
                print("Conteneur Docker arrêté avec succès.", flush=True)
                print("Suppression du conteneur Docker...", flush=True)
                # Supprimer le conteneur Docker
                rm_result = subprocess.run(
                    ["docker", "rm", container_id],
                    capture_output=True,
                    text=True
                )
                if rm_result.returncode == 0:
                    print("Conteneur Docker supprimé avec succès.", flush=True)
                else:
                    print("Erreur lors de la suppression du conteneur Docker.")
                    print(rm_result.stdout)
                    print(rm_result.stderr)
                    exit(rm_result.returncode)
                # Lancement du conteneur Docker
                print("Lancement de l'ancien conteneur...", flush=True)
                run_result = subprocess.run(
                ["docker", "run", "-p", "8080:8080","-d","--name", f"app_container_rollback",f"app_old"],
                    capture_output=True,
                    text=True,
                    shell=False  
                )
                if run_result.returncode == 0:
                    print("Docker : Rollback effectué avec succcès !", flush=True)
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
            print("Aucun conteneur Docker n'est en cours d'exécution.", flush=True)
    else:
        print("Erreur lors de la récupération de l'ID du conteneur Docker.")
        print(result.stderr)
        exit(result.returncode)

def sonar_check():
    """Lance l'analyse du code via SonarQube."""
    print("Analyse du code en cours...", flush=True)

    # Définition de la commande sonar-scanner
    sonar_command = [
        "/usr/local/sonar-scanner-6.2.1.4610-linux-x64/bin/sonar-scanner",
        "-Dsonar.projectKey=PCS",
        "-Dsonar.sources=src/main/java",
        "-Dsonar.java.binaries=target/classes",
        "-Dsonar.host.url=http://localhost:9000",
        "-Dsonar.token=sqp_f0634a9a71da9e04fc44e72daa6e6435abb39766"
    ]

    # Exécution de la commande et capture de la sortie
    result = subprocess.run(sonar_command, capture_output=True, text=True)
    # Affichage du résultat
    if result.returncode == 0:
        print("Analyse SonarQube réussie !", flush=True)
        print("Attente des résultats de l'Analyse (30s)", flush=True)
        time.sleep(30)
        # Une fois l'analyse terminée, interroger les issues sur SonarQube
        status = get_sonar_issues()
        if status:
            print("Aucun problème de criticité HIGH ou BLOCKER n'a été détécté", flush=True)
            return status
        else:
            print("Un problème de criticité HIGH ou BLOCKER a été détécté. Le déploiement du code ne peut s'effectuer... Pour plus se rendre sur SonarQube.", flush=True)
            return status
    else:
        print("Erreur lors de l'analyse SonarQube.", flush=True)

def get_sonar_issues():
    """Récupère les issues (bugs, vulnérabilités, smells) du projet via l'API SonarQube."""
    # Authentification avec le token SonarQube
    auth = HTTPBasicAuth('squ_5d90800e0dd7ae983fb4cb10d1ecad57eb9fa440', '')  # Le token en guise de mot de passe

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
        print("Erreur lors de la récupération des issues.", flush=True)
        print("Code de réponse:", response.status_code)

def test_penetration():
    try:
        
        print("En attente du démarrage de l'application (30s)", flush=True)
        time.sleep(40)
        # Start the scan
        scan_url = "http://localhost:8000/JSON/ascan/action/scan/?url=http://127.0.0.1:8080&apikey="
        requests.get(scan_url)
        print("Début du scan...")
        # Wait for scan completion
        response_status = requests.get("http://localhost:8000/JSON/ascan/view/status/").json()
        status = response_status.get('status')
        if status == '100':  # Scan complete
            print("Scan de sécurité réussi", flush=True)
        # Fetch the scan results
        report_url = "http://localhost:8000/OTHER/core/other/jsonreport/?apikey="
        scan_json = requests.get(report_url).json()

        # Check for high or medium risks
        sites = scan_json.get("site", [])
        if not sites:
            print("Site non trouvé.", flush=True)
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
                    print(f"Risk detected: {risk_desc}", flush=True)
                    break
        if high:
            print("Le test de pénétration a échoué, rollback en cours", flush=True)
            return False
        else:
            print("Le test de pénétration a réussi, pas de failles majeures détectées", flush=True)
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
        print("Suppression du dossier existant.", flush=True)
    print("Clonage du projet...", flush=True)
    git.Git().clone("https://github.com/Ertenox/Tuto-Web-service.git")
    os.chdir("/home/cicd/PCS/Tuto-Web-service")
    run_maven()
    if sonar_check():
        os.chdir("/home/cicd/PCS")
        run_docker()
      
    if test_penetration() == False or test_livre_api.run_tests() == False:
        rollback.rollback_docker()
    