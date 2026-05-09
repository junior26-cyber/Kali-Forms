# KaliForms

**KaliForms** est une plateforme web moderne et professionnelle de création de sondages et de collecte de données, conçue avec Django. Inspirée par la simplicité de Google Forms, elle offre une interface épurée, sécurisée et totalement responsive pour les entreprises et les particuliers.

## 🚀 Fonctionnalités Clés

### 📊 Tableau de Bord Utilisateur
- Vue d'ensemble de tous les formulaires créés.
- Indicateurs en temps réel du nombre de réponses par sondage.
- Actions rapides : Création, Édition, Suppression et accès direct aux Résultats.

### 🛠️ Builder de Sondages Intuitif
- Interface de construction dynamique.
- **6 types de questions supportés** : 
    - Texte court et Texte long.
    - Choix multiple (Radio) et Cases à cocher.
    - Liste déroulante (Select).
    - Oui/Non (Booléen).
- Gestion des questions obligatoires.
- Ajout/Suppression d'options à la volée.

### 📈 Analyse des Résultats
- **Résumé Statistique** : Visualisation automatique sous forme de graphiques de progression et calcul des pourcentages.
- **Réponses Individuelles** : Tableau détaillé de chaque soumission pour une analyse granulaire.
- **Lien de partage unique** pour chaque sondage.

### 🔐 Sécurité & Authentification
- Système d'inscription et de connexion sécurisé (par email).
- Protection contre les attaques CSRF.
- Isolation stricte des données : les utilisateurs n'accèdent qu'à leurs propres sondages.

## 🛠️ Stack Technique

- **Backend** : Django 4.2+ (Python)
- **Frontend** : HTML5, Vanilla CSS (Design moderne "Airy"), JavaScript (ES6)
- **Base de données** : SQLite (Développement), prêt pour PostgreSQL (Production)
- **Déploiement** : Compatible Gunicorn, Whitenoise et variables d'environnement (.env)

## 📦 Installation Locale

1. **Cloner le dépôt** :
   ```bash
   git clone https://github.com/junior26-cyber/Kali-Forms.git
   cd Kali-Forms
   ```

2. **Créer un environnement virtuel** :
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Installer les dépendances** :
   ```bash
   pip install -r requirements.txt
   ```

4. **Appliquer les migrations** :
   ```bash
   python iot/manage.py migrate
   ```

5. **Lancer le serveur** :
   ```bash
   python iot/manage.py runserver
   ```
   Accédez à l'application via `http://127.0.0.1:8000`.

## 🌐 Hébergement

Le projet est pré-configuré pour un déploiement rapide sur des plateformes comme **Render**, **Railway** ou **Heroku**.
- Utilisez `Whitenoise` pour servir les fichiers statiques.
- Configurez vos variables d'environnement (`SECRET_KEY`, `DEBUG`, `DATABASE_URL`) sur votre hébergeur.

---
Développé avec passion par [Junior](https://github.com/junior26-cyber).
