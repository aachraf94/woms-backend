# WOMS Backend

Dépôt contenant le code source de l'API et des services métiers du WOMS (Well Operations Management System). Développé en Django avec PostgreSQL.

## Features

- **Accounts**: Gestion des utilisateurs, authentification et autorisations
- **Wells**: Gestion des puits, opérations, et rapports journaliers
- **Dashboard**: Visualisation interactive des données
- **Analytics**: Analyse et comparaison des données
- **Alerts**: Système de notification et détection d'anomalies
- **History**: Suivi historique des opérations

## Installation

1. Cloner le dépôt
2. Créer un environnement virtuel: `python -m venv venv`
3. Activer l'environnement virtuel:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
4. Installer les dépendances: `pip install -r requirements.txt`
5. Copier `.env.example` vers `.env` et configurer les variables d'environnement
6. Exécuter les migrations: `python manage.py migrate`
7. Créer un super utilisateur: `python manage.py createsuperadmin --email admin@example.com --password secure_password`
8. Lancer le serveur: `python manage.py runserver`

## Documentation API

La documentation API est disponible à l'adresse `/api/docs/` une fois le serveur lancé.
