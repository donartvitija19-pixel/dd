# AVALANT Manager - Deployment në Coolify

## Përgatitja e Projektit

### 1. Push në GitHub
```bash
git init
git add .
git commit -m "Initial commit - AVALANT Manager"
git remote add origin https://github.com/your-username/avalant-manager.git
git push -u origin main
```

### 2. Setup në Coolify

#### A. Krijo Project të Ri
1. Login në Coolify dashboard
2. Krijo projekt të ri: "AVALANT Manager"
3. Zgjidh "Docker Compose" si deployment type

#### B. Konfigurimet e Repository
1. Connect GitHub repository
2. Branch: `main`
3. Docker Compose file: `docker-compose.yml`

#### C. Environment Variables
Shko te **Environment** dhe shto:

```env
# Database
MONGO_URL=mongodb://mongodb:27017
DB_NAME=avalant_manager

# Security (NDRYSHOJE!)
JWT_SECRET_KEY=GJENERONI-NJE-SECRET-KEY-TE-FORTE-KETU

# CORS
CORS_ORIGINS=https://your-domain.com

# Frontend
REACT_APP_BACKEND_URL=https://your-domain.com
```

**RËNDËSI:** Gjeneroni JWT_SECRET_KEY të fortë:
```bash
# Në terminal:
openssl rand -hex 32
```

#### D. Domain Configuration
1. Shko te **Domains**
2. Shto domain-in tuaj: `avalant.your-domain.com`
3. Enable SSL/TLS (Coolify e bën automatikisht me Let's Encrypt)

#### E. Deploy
1. Kliko "Deploy"
2. Prit 5-10 minuta për build
3. Kontrollo logs nëse ka gabime

---

## Verifikimi pas Deployment

### Health Checks
```bash
# Backend
curl https://your-domain.com/health

# Frontend
curl https://your-domain.com
```

### Krijoni Admin User
Pas deployment-it, duhet të krijoni admin user në MongoDB:

1. Hyr në MongoDB container:
```bash
docker exec -it avalant-mongodb mongosh
```

2. Krijo admin:
```javascript
use avalant_manager

db.users.insertOne({
  "id": "admin-001",
  "email": "admin@avalant.com",
  "emri": "Admin",
  "mbiemri": "User",
  "role": "admin",
  "password_hash": "$2b$12$...", // Gjeneroni me bcrypt
  "created_at": new Date().toISOString()
})
```

Ose përdorni këtë Python script:
```python
import bcrypt

password = "admin123"
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
print(hashed.decode('utf-8'))
```

---

## Troubleshooting

### Problem: Backend nuk lidhet me MongoDB
**Zgjidhje:** Sigurohu që `MONGO_URL=mongodb://mongodb:27017` (emri i service në docker-compose)

### Problem: Frontend nuk gjen backend
**Zgjidhje:** Ndryshoni `REACT_APP_BACKEND_URL` me domain-in e saktë të backend

### Problem: CORS errors
**Zgjidhje:** Shto domain-in e frontend në `CORS_ORIGINS`

---

## Backup & Maintenance

### MongoDB Backup
```bash
# Export database
docker exec avalant-mongodb mongodump --db avalant_manager --out /backup

# Import database
docker exec avalant-mongodb mongorestore --db avalant_manager /backup/avalant_manager
```

### Logs
```bash
# Backend logs
docker logs avalant-backend -f

# Frontend logs
docker logs avalant-frontend -f

# MongoDB logs
docker logs avalant-mongodb -f
```

---

## Përditësime

1. Push ndryshimet në GitHub:
```bash
git add .
git commit -m "Update feature"
git push
```

2. Në Coolify, kliko "Redeploy"

---

## Support

Për pyetje:
- Email: admin@avalant.com
- Logs: `/var/log/` në containers
