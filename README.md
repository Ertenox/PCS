# PCS

Projet réalisé dans le cadre du module Cloud Sécurisé à l'Institut Mines-Télécom (IMT).
L'objectif principal est de mettre en place une chaîne CI/CD sécurisée permettant le déploiement automatique d'une application sur une machine virtuelle Linux.

Objectifs du projet
- Adapter une application métier existante à un environnement Dockerisé.
- Mettre en place une plateforme CI/CD avec gestion d’utilisateurs, rôles et pipeline visuel.
- Déployer automatiquement l’application sur une VM via Docker.
- Ajouter des outils de qualité de code (SonarQube) et de sécurité (tests d’intrusion).
- Gérer le rollback en cas d’erreur.

Technologies
- Python 3
- Docker / Docker Compose
- CI/CD : GitHub Actions ou Jenkins
- SonarQube (qualité de code)
- OAuth2 (Google / GitHub) pour l’authentification
- VirtualBox / VM Linux
