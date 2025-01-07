import git
import shutil
import os
import subprocess

def run_maven():
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
    id = os.popen("date +%Y%m%d").read().strip()  # Generate a unique ID based on the current date
    print("Création de l'image docker...")
    result = subprocess.run(
        ["docker", "build", "-t", f"app_{id}", "."],
        capture_output=True,
        text=True,
        shell=False  # Use a list for arguments and avoid `shell=True` for better security
    )
    if result.returncode == 0:
        print("Docker : Image créée avec succès !")

        # Lancement du conteneur Docker
        print("Lancement du conteneur...")
        run_result = subprocess.run(
            ["docker", "run", "-p", "8080:8080", "-d", "--name", f"app_container_{id}", f"app_{id}"],
            capture_output=True,
            text=True,
            shell=False  # Use a list for arguments
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




if __name__ == "__main__":
    if os.path.exists("Tuto-Web-service"):
        os.system("rm -rf Tuto-Web-service")
        print("Suppression du dossier existant.")
    print("Clonage du projet...")
    git.Git().clone("https://github.com/DavidIMT/Tuto-Web-service.git")
    os.chdir("Tuto-Web-service")
    print("Clonage du projet réussi !")
    run_maven()
    os.chdir("..")
    run_docker()


