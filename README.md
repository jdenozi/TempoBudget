# Tempo Budget

Application de gestion de budget personnel et partagé.

## Fonctionnalités

- **Budgets personnels** : Suivi des dépenses par catégories
- **Budgets de groupe** : Partage avec répartition des parts entre membres
- **Transactions récurrentes** : Génération automatique des dépenses mensuelles
- **Projections** : Estimation des dépenses à venir
- **Statistiques** : Répartition par tags (crédit, besoin, loisir, épargne)

## Stack

- **Frontend** : Vue 3 + TypeScript + Naive UI
- **Backend** : FastAPI + SQLite
- **Déploiement** : Docker + Nginx

## Lancement local

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

## Déploiement Docker

```bash
cp .env.example .env
# Éditer .env avec JWT_SECRET généré via: openssl rand -hex 32

docker-compose -f docker-compose.prod.yml up -d
```

L'application est accessible sur le port 80.

## Licence

MIT
