import git
import shutil
import os
import subprocess

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


if __name__ == "__main__":
    #shutil.rmtree("Tuto-Web-service", ignore_errors=True)
    git.Git().clone("https://github.com/DavidIMT/Tuto-Web-service.git")
    os.chdir("Tuto-Web-service")
    run_maven()


