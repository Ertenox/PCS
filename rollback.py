import subprocess


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

if __name__ == "__main__":
    rollback_docker() 