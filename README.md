# AVALANT Manager

Sistem i plotë menaxhimi financiar dhe biznesi me light theme, RBAC, dhe 12 module.

## 🚀 Quick Start

### Opsioni 1: Coolify (Rekomanduar për Production)
Shiko [COOLIFY_DEPLOYMENT.md](./COOLIFY_DEPLOYMENT.md) për udhëzime të detajuara.

### Opsioni 2: Local Development

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn server:app --reload --port 8001

# Frontend (terminal i ri)
cd frontend
yarn install
yarn start
```

## 📦 Stack Teknologjik

- **Backend:** FastAPI (Python 3.11)
- **Frontend:** React 18 + Tailwind CSS
- **Database:** MongoDB
- **Auth:** JWT tokens (24h expiry)
- **UI Components:** Shadcn/UI

## 🎯 Features

### 12 Module:
1. **Dashboard** - Overview financiar me stats
2. **Borxhe** - Menaxhimi i obligimeve (CashPlus, RBKO, Tjera)
3. **Shpenzime** - Tracking me 5 kategori + CSV export
4. **Financa Ditore** - Input ditor + analytics
5. **Stock/Inventari** - Auto-sync me fatura
6. **Llogaritë Bankare** - Tracking i 3+ llogarive
7. **Fatura** - Blerje & Shitje me Excel export
8. **Deklarime & Pagat** - Tremujore + tracking mujor
9. **CRM** - Baza e klientëve me Smart Clean
10. **CRM-CPP** - Cost Per Performance analytics
11. **Kursime** - Progress tracking + depozitim history
12. **Kontabilistët** - User management
13. **Settings** - Full database backup export

### RBAC (Role-Based Access Control):
- **Admin:** Full access në të gjitha modulet
- **Kontabilist:** Limited access (Stock read-only, Fatura CRUD, Deklarimet CRUD)

## 🔐 Kredenciale Default

**Admin:**
- Email: `admin@avalant.com`
- Password: `admin123`

**Kontabilist:**
- Email: `kontabilist@avalant.com`
- Password: `kont123`

⚠️ **NDRYSHONI këto në production!**

## 🛠️ Environment Variables

```env
# Backend
MONGO_URL=mongodb://localhost:27017
DB_NAME=avalant_manager
JWT_SECRET_KEY=your-secret-key
CORS_ORIGINS=http://localhost:3000

# Frontend
REACT_APP_BACKEND_URL=http://localhost:8001
```

## 🚢 Deployment në Coolify

Shiko [COOLIFY_DEPLOYMENT.md](./COOLIFY_DEPLOYMENT.md) për udhëzime step-by-step.

---

Built with ❤️ for efficient financial management
