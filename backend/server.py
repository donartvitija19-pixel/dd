from fastapi import FastAPI, APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Optional, List
import os
import logging
import bcrypt
from jose import JWTError, jwt
from pydantic import BaseModel, Field, ConfigDict, EmailStr
import uuid
from io import BytesIO
import openpyxl
from fastapi.responses import StreamingResponse
import json

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

app = FastAPI()
api_router = APIRouter(prefix="/api")

SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'avalant-secret-key-2024')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24

security = HTTPBearer()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============ MODELS ============

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    emri: str
    mbiemri: str
    role: str = "kontabilist"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    emri: str
    mbiemri: str
    role: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: User

class BorxhCreate(BaseModel):
    emri: str
    shuma_totale: float
    data_kestit: str
    tipi: str

class Borxh(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    emri: str
    shuma_totale: float
    data_kestit: str
    shuma_paguar: float = 0.0
    shuma_mbetur: float
    tipi: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ShpenzimCreate(BaseModel):
    kategoria: str
    pershkrimi: str
    shuma: float
    data: str
    borxh_id: Optional[str] = None

class Shpenzim(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    kategoria: str
    pershkrimi: str
    shuma: float
    data: str
    borxh_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None

class FinancaDitoreCreate(BaseModel):
    data: str
    cash: float
    banka: float
    fb_ads: float
    porosi_krijuar: float
    porosi_ne_depo: float
    porosi_ne_dergim: float
    porosi_dorezuar: float
    porosi_ne_pritje: float
    shenime: Optional[str] = ""

class FinancaDitore(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    data: str
    cash: float
    banka: float
    fb_ads: float
    porosi_krijuar: float
    porosi_ne_depo: float
    porosi_ne_dergim: float
    porosi_dorezuar: float
    porosi_ne_pritje: float
    gjendja_fund_dite: float
    shenime: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StockCreate(BaseModel):
    emri_produktit: str
    sku: str
    sasia: int

class Stock(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    emri_produktit: str
    sku: str
    sasia: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class FaturaProdukt(BaseModel):
    emri: str
    sasia: int
    cmimi: float

class FaturaCreate(BaseModel):
    tipi: str
    furnitori: str
    nui: Optional[str] = ""
    nr_fatures: str
    produktet: List[FaturaProdukt]
    data: str

class Fatura(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tipi: str
    furnitori: str
    nui: str
    nr_fatures: str
    produktet: List[FaturaProdukt]
    vlera_totale: float
    data: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DeklarimCreate(BaseModel):
    tremujori: str
    viti: int
    vlera_shitese: float
    data_deklarimit: str

class Deklarim(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tremujori: str
    viti: int
    vlera_shitese: float
    data_deklarimit: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class PagaCreate(BaseModel):
    emri: str
    mbiemri: str
    nr_personal: str
    vlera: float
    muaji: str
    viti: int

class Paga(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    emri: str
    mbiemri: str
    nr_personal: str
    vlera: float
    muaji: str
    viti: int
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CRMCreate(BaseModel):
    emri: str
    mbiemri: str
    telefon: str
    adresa: Optional[str] = ""
    shenime: Optional[str] = ""

class CRM(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    emri: str
    mbiemri: str
    telefon: str
    adresa: str
    shenime: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class CRMCPPCreate(BaseModel):
    data: str
    sponzor: float
    porosi: int
    mesazhe: int
    kosto_blerese: float
    vlera_shitese: float
    produkti: str
    platforma: str

class CRMCPP(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    data: str
    sponzor: float
    porosi: int
    mesazhe: int
    kosto_blerese: float
    vlera_shitese: float
    produkti: str
    platforma: str
    cost_per_order: float
    sponzor_per_mesazhe: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DepozitimEntry(BaseModel):
    data: str
    vlera: float
    status: str

class KursimCreate(BaseModel):
    qellimi: str
    shuma_target: float
    shuma_aktuale: float = 0.0

class Kursim(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    qellimi: str
    shuma_target: float
    shuma_aktuale: float
    depozitimi_history: List[DepozitimEntry] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DepozitimRequest(BaseModel):
    kursim_id: str
    vlera: Optional[float] = None
    status: str

class BankaAccountCreate(BaseModel):
    emri_bankes: str
    bilanci: float

class BankaAccount(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    emri_bankes: str
    bilanci: float
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# ============ AUTH FUNCTIONS ============

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise HTTPException(status_code=401, detail="Token i pavlefshëm")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token i pavlefshëm")
    
    user = await db.users.find_one({"email": email}, {"_id": 0})
    if user is None:
        raise HTTPException(status_code=401, detail="Përdoruesi nuk u gjet")
    return User(**user)

async def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Qasje e ndaluar: Vetëm Admin")
    return current_user

async def require_admin_or_kontabilist(current_user: User = Depends(get_current_user)):
    if current_user.role not in ["admin", "kontabilist"]:
        raise HTTPException(status_code=403, detail="Qasje e ndaluar")
    return current_user

# ============ AUTH ENDPOINTS ============

@api_router.post("/auth/register", response_model=User)
async def register(user_data: UserCreate, current_user: User = Depends(require_admin)):
    existing = await db.users.find_one({"email": user_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email-i ekziston tashmë")
    
    # Create the document to insert with password_hash
    doc = {
        "id": str(uuid.uuid4()),
        "email": user_data.email,
        "emri": user_data.emri,
        "mbiemri": user_data.mbiemri,
        "role": user_data.role,
        "password_hash": hash_password(user_data.password),
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(doc)
    
    # Return user without password_hash
    user_data_clean = {k: v for k, v in doc.items() if k not in ['_id', 'password_hash']}
    return User(**user_data_clean)

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user_doc = await db.users.find_one({"email": credentials.email})
    if not user_doc:
        raise HTTPException(status_code=401, detail="Email ose fjalëkalim i gabuar")
    
    if not verify_password(credentials.password, user_doc.get('password_hash', '')):
        raise HTTPException(status_code=401, detail="Email ose fjalëkalim i gabuar")
    
    access_token = create_access_token(data={"sub": user_doc['email']})
    
    # Remove sensitive fields before creating User object
    user_data = {k: v for k, v in user_doc.items() if k not in ['_id', 'password_hash']}
    user = User(**user_data)
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=user
    )

@api_router.get("/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# ============ DASHBOARD ============

@api_router.get("/dashboard")
async def get_dashboard(current_user: User = Depends(require_admin)):
    # Financa Ditore - latest
    financa_list = await db.financa_ditore.find({}, {"_id": 0}).sort("data", -1).to_list(1000)
    
    gjendja_totale = 0.0
    bilanci_aktual = 0.0
    if financa_list:
        gjendja_totale = financa_list[0].get('gjendja_fund_dite', 0)
        if len(financa_list) > 1:
            gjendja_fillestare = financa_list[-1].get('gjendja_fund_dite', 0)
            bilanci_aktual = gjendja_totale - gjendja_fillestare
        else:
            bilanci_aktual = gjendja_totale
    
    # Borxhe total
    borxhe_list = await db.borxhe.find({}, {"_id": 0}).to_list(1000)
    total_borxhe = sum(b.get('shuma_mbetur', 0) for b in borxhe_list)
    
    # Kursime progress
    kursime_list = await db.kursime.find({}, {"_id": 0}).to_list(1000)
    kursime_progress = 0
    if kursime_list:
        total_target = sum(k.get('shuma_target', 0) for k in kursime_list)
        total_aktual = sum(k.get('shuma_aktuale', 0) for k in kursime_list)
        if total_target > 0:
            kursime_progress = (total_aktual / total_target) * 100
    
    # Shpenzime te papritura count
    from datetime import datetime
    current_month = datetime.now().strftime("%Y-%m")
    shpenzime_papritur = await db.shpenzime.count_documents({
        "kategoria": "Shpenzim i Papritur",
        "data": {"$regex": f"^{current_month}"}
    })
    
    # Shpenzime mujore per kategori
    shpenzime_list = await db.shpenzime.find({
        "data": {"$regex": f"^{current_month}"}
    }, {"_id": 0}).to_list(1000)
    
    shpenzime_nafte = sum(s.get('shuma', 0) for s in shpenzime_list if s.get('kategoria') == 'Derivate')
    shpenzime_familjare = sum(s.get('shuma', 0) for s in shpenzime_list if s.get('kategoria') == 'Familjare')
    
    # Banka accounts
    banka_accounts = await db.banka_accounts.find({}, {"_id": 0}).to_list(10)
    
    # Recent transactions (5 te fundit nga financa ditore)
    recent_transactions = financa_list[:5] if financa_list else []
    
    return {
        "gjendja_totale": round(gjendja_totale, 2),
        "bilanci_aktual": round(bilanci_aktual, 2),
        "total_borxhe": round(total_borxhe, 2),
        "kursime_progress": round(kursime_progress, 2),
        "shpenzime_papritur_count": shpenzime_papritur,
        "shpenzime_nafte_muaj": round(shpenzime_nafte, 2),
        "shpenzime_familjare_muaj": round(shpenzime_familjare, 2),
        "banka_accounts": banka_accounts,
        "recent_transactions": recent_transactions
    }

# ============ BORXHE ============

@api_router.post("/borxhe", response_model=Borxh)
async def create_borxh(data: BorxhCreate, current_user: User = Depends(require_admin)):
    borxh = Borxh(**data.model_dump(), shuma_mbetur=data.shuma_totale)
    doc = borxh.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.borxhe.insert_one(doc)
    return borxh

@api_router.get("/borxhe", response_model=List[Borxh])
async def get_borxhe(current_user: User = Depends(require_admin)):
    borxhe = await db.borxhe.find({}, {"_id": 0}).to_list(1000)
    return borxhe

@api_router.put("/borxhe/{borxh_id}", response_model=Borxh)
async def update_borxh(borxh_id: str, data: BorxhCreate, current_user: User = Depends(require_admin)):
    update_data = data.model_dump()
    update_data['shuma_mbetur'] = data.shuma_totale - (await db.borxhe.find_one({"id": borxh_id}, {"_id": 0}) or {}).get('shuma_paguar', 0)
    
    await db.borxhe.update_one({"id": borxh_id}, {"$set": update_data})
    updated = await db.borxhe.find_one({"id": borxh_id}, {"_id": 0})
    return Borxh(**updated)

@api_router.delete("/borxhe/{borxh_id}")
async def delete_borxh(borxh_id: str, current_user: User = Depends(require_admin)):
    await db.borxhe.delete_one({"id": borxh_id})
    return {"message": "Borxhi u fshi me sukses"}

# ============ SHPENZIME ============

@api_router.post("/shpenzime", response_model=Shpenzim)
async def create_shpenzim(data: ShpenzimCreate, current_user: User = Depends(require_admin)):
    shpenzim = Shpenzim(**data.model_dump())
    doc = shpenzim.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    
    # Auto-update borxh if kategoria is Borgje
    if data.kategoria == "Borgje" and data.borxh_id:
        borxh = await db.borxhe.find_one({"id": data.borxh_id}, {"_id": 0})
        if borxh:
            new_paguar = borxh['shuma_paguar'] + data.shuma
            new_mbetur = borxh['shuma_totale'] - new_paguar
            await db.borxhe.update_one(
                {"id": data.borxh_id},
                {"$set": {"shuma_paguar": new_paguar, "shuma_mbetur": new_mbetur}}
            )
    
    await db.shpenzime.insert_one(doc)
    return shpenzim

@api_router.get("/shpenzime", response_model=List[Shpenzim])
async def get_shpenzime(kategoria: Optional[str] = None, data_filter: Optional[str] = None, current_user: User = Depends(require_admin)):
    query = {}
    if kategoria:
        query['kategoria'] = kategoria
    if data_filter:
        query['data'] = {"$regex": f"^{data_filter}"}
    
    shpenzime = await db.shpenzime.find(query, {"_id": 0}).to_list(1000)
    return shpenzime

@api_router.put("/shpenzime/{shpenzim_id}", response_model=Shpenzim)
async def update_shpenzim(shpenzim_id: str, data: ShpenzimCreate, current_user: User = Depends(require_admin)):
    update_data = data.model_dump()
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.shpenzime.update_one({"id": shpenzim_id}, {"$set": update_data})
    updated = await db.shpenzime.find_one({"id": shpenzim_id}, {"_id": 0})
    return Shpenzim(**updated)

@api_router.delete("/shpenzime/{shpenzim_id}")
async def delete_shpenzim(shpenzim_id: str, current_user: User = Depends(require_admin)):
    await db.shpenzime.delete_one({"id": shpenzim_id})
    return {"message": "Shpenzimi u fshi me sukses"}

@api_router.get("/shpenzime/export/csv")
async def export_shpenzime_csv(current_user: User = Depends(require_admin)):
    shpenzime = await db.shpenzime.find({}, {"_id": 0}).to_list(10000)
    
    from io import StringIO
    import csv
    
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=['id', 'kategoria', 'pershkrimi', 'shuma', 'data', 'borxh_id'])
    writer.writeheader()
    for s in shpenzime:
        writer.writerow({
            'id': s.get('id', ''),
            'kategoria': s.get('kategoria', ''),
            'pershkrimi': s.get('pershkrimi', ''),
            'shuma': s.get('shuma', 0),
            'data': s.get('data', ''),
            'borxh_id': s.get('borxh_id', '')
        })
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=shpenzime.csv"}
    )

# ============ FINANCA DITORE ============

@api_router.post("/financa-ditore", response_model=FinancaDitore)
async def create_financa_ditore(data: FinancaDitoreCreate, current_user: User = Depends(require_admin)):
    gjendja = (data.cash + data.banka + data.fb_ads + 
               data.porosi_krijuar + data.porosi_ne_depo + data.porosi_ne_dergim + 
               data.porosi_dorezuar + data.porosi_ne_pritje)
    financa = FinancaDitore(**data.model_dump(), gjendja_fund_dite=gjendja)
    doc = financa.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.financa_ditore.insert_one(doc)
    return financa

@api_router.get("/financa-ditore", response_model=List[FinancaDitore])
async def get_financa_ditore(data_filter: Optional[str] = None, current_user: User = Depends(require_admin)):
    query = {}
    if data_filter:
        query['data'] = {"$regex": f"^{data_filter}"}
    
    financa = await db.financa_ditore.find(query, {"_id": 0}).sort("data", -1).to_list(1000)
    return financa

@api_router.get("/financa-ditore/analytics")
async def get_financa_analytics(current_user: User = Depends(require_admin)):
    financa_list = await db.financa_ditore.find({}, {"_id": 0}).sort("data", -1).to_list(1000)
    
    if not financa_list:
        return {
            "total_cash": 0,
            "total_banka": 0,
            "total_fb_ads": 0,
            "gjendja_latest": 0,
            "diferenca_dite": 0,
            "dite_pozitive": 0,
            "dite_negative": 0
        }
    
    # Vlerat e ditës më të fundit (jo totalet)
    latest_entry = financa_list[0]
    total_cash = latest_entry.get('cash', 0)
    total_banka = latest_entry.get('banka', 0)
    total_fb_ads = latest_entry.get('fb_ads', 0)
    gjendja_latest = latest_entry.get('gjendja_fund_dite', 0)
    
    diferenca = 0
    if len(financa_list) > 1:
        diferenca = financa_list[0].get('gjendja_fund_dite', 0) - financa_list[1].get('gjendja_fund_dite', 0)
    
    dite_pozitive = 0
    dite_negative = 0
    for i in range(len(financa_list) - 1):
        if financa_list[i].get('gjendja_fund_dite', 0) > financa_list[i+1].get('gjendja_fund_dite', 0):
            dite_pozitive += 1
        else:
            dite_negative += 1
    
    return {
        "total_cash": round(total_cash, 2),
        "total_banka": round(total_banka, 2),
        "total_fb_ads": round(total_fb_ads, 2),
        "gjendja_latest": round(gjendja_latest, 2),
        "diferenca_dite": round(diferenca, 2),
        "dite_pozitive": dite_pozitive,
        "dite_negative": dite_negative
    }

@api_router.put("/financa-ditore/{financa_id}", response_model=FinancaDitore)
async def update_financa_ditore(financa_id: str, data: FinancaDitoreCreate, current_user: User = Depends(require_admin)):
    gjendja = (data.cash + data.banka + data.fb_ads + 
               data.porosi_krijuar + data.porosi_ne_depo + data.porosi_ne_dergim + 
               data.porosi_dorezuar + data.porosi_ne_pritje)
    update_data = data.model_dump()
    update_data['gjendja_fund_dite'] = gjendja
    
    await db.financa_ditore.update_one({"id": financa_id}, {"$set": update_data})
    updated = await db.financa_ditore.find_one({"id": financa_id}, {"_id": 0})
    return FinancaDitore(**updated)

@api_router.delete("/financa-ditore/{financa_id}")
async def delete_financa_ditore(financa_id: str, current_user: User = Depends(require_admin)):
    await db.financa_ditore.delete_one({"id": financa_id})
    return {"message": "Financa ditore u fshi me sukses"}

# ============ STOCK ============

@api_router.post("/stock", response_model=Stock)
async def create_stock(data: StockCreate, current_user: User = Depends(require_admin)):
    existing = await db.stock.find_one({"sku": data.sku}, {"_id": 0})
    if existing:
        raise HTTPException(status_code=400, detail="SKU ekziston tashmë")
    
    stock = Stock(**data.model_dump())
    doc = stock.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.stock.insert_one(doc)
    return stock

@api_router.get("/stock", response_model=List[Stock])
async def get_stock(current_user: User = Depends(get_current_user)):
    stock_list = await db.stock.find({}, {"_id": 0}).to_list(1000)
    return stock_list

@api_router.put("/stock/{stock_id}", response_model=Stock)
async def update_stock(stock_id: str, data: StockCreate, current_user: User = Depends(require_admin)):
    await db.stock.update_one({"id": stock_id}, {"$set": data.model_dump()})
    updated = await db.stock.find_one({"id": stock_id}, {"_id": 0})
    return Stock(**updated)

@api_router.delete("/stock/{stock_id}")
async def delete_stock(stock_id: str, current_user: User = Depends(require_admin)):
    await db.stock.delete_one({"id": stock_id})
    return {"message": "Produkti u fshi me sukses"}

# ============ FATURA ============

@api_router.post("/fatura", response_model=Fatura)
async def create_fatura(data: FaturaCreate, current_user: User = Depends(require_admin_or_kontabilist)):
    vlera_totale = sum(p.sasia * p.cmimi for p in data.produktet)
    fatura = Fatura(**data.model_dump(), vlera_totale=vlera_totale)
    doc = fatura.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['produktet'] = [p.model_dump() for p in fatura.produktet]
    
    # Update stock
    for produkt in data.produktet:
        stock_item = await db.stock.find_one({"emri_produktit": produkt.emri}, {"_id": 0})
        if stock_item:
            if data.tipi == "Blerje":
                new_sasia = stock_item['sasia'] + produkt.sasia
            else:  # Shitje
                new_sasia = stock_item['sasia'] - produkt.sasia
            await db.stock.update_one({"id": stock_item['id']}, {"$set": {"sasia": new_sasia}})
    
    await db.fatura.insert_one(doc)
    return fatura

@api_router.get("/fatura", response_model=List[Fatura])
async def get_fatura(tipi: Optional[str] = None, time_filter: Optional[str] = None, current_user: User = Depends(require_admin_or_kontabilist)):
    query = {}
    if tipi:
        query['tipi'] = tipi
    if time_filter:
        query['data'] = {"$regex": f"^{time_filter}"}
    
    fatura_list = await db.fatura.find(query, {"_id": 0}).sort("data", -1).to_list(1000)
    return fatura_list

@api_router.put("/fatura/{fatura_id}", response_model=Fatura)
async def update_fatura(fatura_id: str, data: FaturaCreate, current_user: User = Depends(require_admin_or_kontabilist)):
    vlera_totale = sum(p.sasia * p.cmimi for p in data.produktet)
    update_data = data.model_dump()
    update_data['vlera_totale'] = vlera_totale
    update_data['produktet'] = [p.model_dump() for p in data.produktet]
    
    await db.fatura.update_one({"id": fatura_id}, {"$set": update_data})
    updated = await db.fatura.find_one({"id": fatura_id}, {"_id": 0})
    return Fatura(**updated)

@api_router.delete("/fatura/{fatura_id}")
async def delete_fatura(fatura_id: str, current_user: User = Depends(require_admin_or_kontabilist)):
    await db.fatura.delete_one({"id": fatura_id})
    return {"message": "Fatura u fshi me sukses"}

@api_router.get("/fatura/export/excel")
async def export_fatura_excel(time_filter: Optional[str] = None, current_user: User = Depends(require_admin_or_kontabilist)):
    query = {}
    if time_filter:
        query['data'] = {"$regex": f"^{time_filter}"}
    
    fatura_list = await db.fatura.find(query, {"_id": 0}).to_list(10000)
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Fatura"
    
    headers = ['ID', 'Tipi', 'Furnitori', 'NUI', 'Nr. Fatures', 'Vlera Totale', 'Data']
    ws.append(headers)
    
    for f in fatura_list:
        ws.append([
            f.get('id', ''),
            f.get('tipi', ''),
            f.get('furnitori', ''),
            f.get('nui', ''),
            f.get('nr_fatures', ''),
            f.get('vlera_totale', 0),
            f.get('data', '')
        ])
    
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=fatura.xlsx"}
    )

# ============ DEKLARIMET & PAGAT ============

@api_router.post("/deklarimet", response_model=Deklarim)
async def create_deklarim(data: DeklarimCreate, current_user: User = Depends(require_admin_or_kontabilist)):
    deklarim = Deklarim(**data.model_dump())
    doc = deklarim.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.deklarimet.insert_one(doc)
    return deklarim

@api_router.get("/deklarimet", response_model=List[Deklarim])
async def get_deklarimet(viti: Optional[int] = None, current_user: User = Depends(require_admin_or_kontabilist)):
    query = {}
    if viti:
        query['viti'] = viti
    deklarimet = await db.deklarimet.find(query, {"_id": 0}).to_list(1000)
    return deklarimet

@api_router.get("/deklarimet/analytics/{viti}")
async def get_deklarimet_analytics(viti: int, current_user: User = Depends(require_admin_or_kontabilist)):
    deklarimet = await db.deklarimet.find({"viti": viti}, {"_id": 0}).to_list(100)
    
    tm_totals = {"TM1": 0, "TM2": 0, "TM3": 0, "TM4": 0}
    for d in deklarimet:
        tm = d.get('tremujori', '')
        if tm in tm_totals:
            tm_totals[tm] += d.get('vlera_shitese', 0)
    
    return tm_totals

@api_router.put("/deklarimet/{deklarim_id}", response_model=Deklarim)
async def update_deklarim(deklarim_id: str, data: DeklarimCreate, current_user: User = Depends(require_admin_or_kontabilist)):
    await db.deklarimet.update_one({"id": deklarim_id}, {"$set": data.model_dump()})
    updated = await db.deklarimet.find_one({"id": deklarim_id}, {"_id": 0})
    return Deklarim(**updated)

@api_router.delete("/deklarimet/{deklarim_id}")
async def delete_deklarim(deklarim_id: str, current_user: User = Depends(require_admin_or_kontabilist)):
    await db.deklarimet.delete_one({"id": deklarim_id})
    return {"message": "Deklarimi u fshi me sukses"}

@api_router.post("/pagat", response_model=Paga)
async def create_paga(data: PagaCreate, current_user: User = Depends(require_admin_or_kontabilist)):
    paga = Paga(**data.model_dump())
    doc = paga.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.pagat.insert_one(doc)
    return paga

@api_router.get("/pagat", response_model=List[Paga])
async def get_pagat(viti: Optional[int] = None, current_user: User = Depends(require_admin_or_kontabilist)):
    query = {}
    if viti:
        query['viti'] = viti
    pagat = await db.pagat.find(query, {"_id": 0}).to_list(1000)
    return pagat

@api_router.get("/pagat/analytics/{viti}")
async def get_pagat_analytics(viti: int, current_user: User = Depends(require_admin_or_kontabilist)):
    pagat = await db.pagat.find({"viti": viti}, {"_id": 0}).to_list(1000)
    total = sum(p.get('vlera', 0) for p in pagat)
    return {"total_pagat": round(total, 2)}

@api_router.put("/pagat/{paga_id}", response_model=Paga)
async def update_paga(paga_id: str, data: PagaCreate, current_user: User = Depends(require_admin_or_kontabilist)):
    await db.pagat.update_one({"id": paga_id}, {"$set": data.model_dump()})
    updated = await db.pagat.find_one({"id": paga_id}, {"_id": 0})
    return Paga(**updated)

@api_router.delete("/pagat/{paga_id}")
async def delete_paga(paga_id: str, current_user: User = Depends(require_admin_or_kontabilist)):
    await db.pagat.delete_one({"id": paga_id})
    return {"message": "Paga u fshi me sukses"}

# ============ CRM ============

@api_router.post("/crm", response_model=CRM)
async def create_crm(data: CRMCreate, current_user: User = Depends(require_admin)):
    crm = CRM(**data.model_dump())
    doc = crm.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.crm.insert_one(doc)
    return crm

@api_router.get("/crm", response_model=List[CRM])
async def get_crm(current_user: User = Depends(require_admin)):
    crm_list = await db.crm.find({}, {"_id": 0}).to_list(10000)
    return crm_list

@api_router.put("/crm/{crm_id}", response_model=CRM)
async def update_crm(crm_id: str, data: CRMCreate, current_user: User = Depends(require_admin)):
    await db.crm.update_one({"id": crm_id}, {"$set": data.model_dump()})
    updated = await db.crm.find_one({"id": crm_id}, {"_id": 0})
    return CRM(**updated)

@api_router.delete("/crm/{crm_id}")
async def delete_crm(crm_id: str, current_user: User = Depends(require_admin)):
    await db.crm.delete_one({"id": crm_id})
    return {"message": "Klienti u fshi me sukses"}

@api_router.post("/crm/import")
async def import_crm_excel(current_user: User = Depends(require_admin)):
    # This endpoint would handle file upload - simplified for now
    return {"message": "Import functionality - requires file upload"}

@api_router.post("/crm/clean")
async def clean_crm_duplicates(current_user: User = Depends(require_admin)):
    crm_list = await db.crm.find({}, {"_id": 0}).to_list(10000)
    
    seen_phones = set()
    duplicates = []
    
    for crm in crm_list:
        phone = crm.get('telefon', '')
        if phone in seen_phones:
            duplicates.append(crm['id'])
        else:
            seen_phones.add(phone)
    
    if duplicates:
        await db.crm.delete_many({"id": {"$in": duplicates}})
    
    return {"message": f"{len(duplicates)} duplikate u fshinë"}

@api_router.get("/crm/export/csv")
async def export_crm_csv(current_user: User = Depends(require_admin)):
    crm_list = await db.crm.find({}, {"_id": 0}).to_list(10000)
    
    from io import StringIO
    import csv
    
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=['id', 'emri', 'mbiemri', 'telefon', 'adresa', 'shenime'])
    writer.writeheader()
    for c in crm_list:
        writer.writerow({
            'id': c.get('id', ''),
            'emri': c.get('emri', ''),
            'mbiemri': c.get('mbiemri', ''),
            'telefon': c.get('telefon', ''),
            'adresa': c.get('adresa', ''),
            'shenime': c.get('shenime', '')
        })
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=crm.csv"}
    )

# ============ CRM CPP ============

@api_router.post("/crm-cpp", response_model=CRMCPP)
async def create_crm_cpp(data: CRMCPPCreate, current_user: User = Depends(require_admin)):
    cost_per_order = data.sponzor / data.porosi if data.porosi > 0 else 0
    sponzor_per_mesazhe = data.sponzor / data.mesazhe if data.mesazhe > 0 else 0
    
    crm_cpp = CRMCPP(
        **data.model_dump(),
        cost_per_order=cost_per_order,
        sponzor_per_mesazhe=sponzor_per_mesazhe
    )
    doc = crm_cpp.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.crm_cpp.insert_one(doc)
    return crm_cpp

@api_router.get("/crm-cpp", response_model=List[CRMCPP])
async def get_crm_cpp(data_filter: Optional[str] = None, current_user: User = Depends(require_admin)):
    query = {}
    if data_filter:
        query['data'] = {"$regex": f"^{data_filter}"}
    
    crm_cpp_list = await db.crm_cpp.find(query, {"_id": 0}).sort("data", -1).to_list(1000)
    return crm_cpp_list

@api_router.put("/crm-cpp/{cpp_id}", response_model=CRMCPP)
async def update_crm_cpp(cpp_id: str, data: CRMCPPCreate, current_user: User = Depends(require_admin)):
    cost_per_order = data.sponzor / data.porosi if data.porosi > 0 else 0
    sponzor_per_mesazhe = data.sponzor / data.mesazhe if data.mesazhe > 0 else 0
    
    update_data = data.model_dump()
    update_data['cost_per_order'] = cost_per_order
    update_data['sponzor_per_mesazhe'] = sponzor_per_mesazhe
    
    await db.crm_cpp.update_one({"id": cpp_id}, {"$set": update_data})
    updated = await db.crm_cpp.find_one({"id": cpp_id}, {"_id": 0})
    return CRMCPP(**updated)

@api_router.delete("/crm-cpp/{cpp_id}")
async def delete_crm_cpp(cpp_id: str, current_user: User = Depends(require_admin)):
    await db.crm_cpp.delete_one({"id": cpp_id})
    return {"message": "Entry u fshi me sukses"}

# ============ KURSIME ============

@api_router.post("/kursime", response_model=Kursim)
async def create_kursim(data: KursimCreate, current_user: User = Depends(require_admin)):
    kursim = Kursim(**data.model_dump())
    doc = kursim.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.kursime.insert_one(doc)
    return kursim

@api_router.get("/kursime", response_model=List[Kursim])
async def get_kursime(current_user: User = Depends(require_admin)):
    kursime_list = await db.kursime.find({}, {"_id": 0}).to_list(1000)
    return kursime_list

@api_router.put("/kursime/{kursim_id}", response_model=Kursim)
async def update_kursim(kursim_id: str, data: KursimCreate, current_user: User = Depends(require_admin)):
    await db.kursime.update_one({"id": kursim_id}, {"$set": data.model_dump()})
    updated = await db.kursime.find_one({"id": kursim_id}, {"_id": 0})
    return Kursim(**updated)

@api_router.delete("/kursime/{kursim_id}")
async def delete_kursim(kursim_id: str, current_user: User = Depends(require_admin)):
    await db.kursime.delete_one({"id": kursim_id})
    return {"message": "Kursimi u fshi me sukses"}

@api_router.post("/kursime/depozitim")
async def add_depozitim(data: DepozitimRequest, current_user: User = Depends(require_admin)):
    kursim = await db.kursime.find_one({"id": data.kursim_id}, {"_id": 0})
    if not kursim:
        raise HTTPException(status_code=404, detail="Kursimi nuk u gjet")
    
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    
    entry = DepozitimEntry(
        data=today,
        vlera=data.vlera or 0,
        status=data.status
    )
    
    history = kursim.get('depozitimi_history', [])
    history.append(entry.model_dump())
    
    new_shuma = kursim['shuma_aktuale']
    if data.status == "depozituar" and data.vlera:
        new_shuma += data.vlera
    
    await db.kursime.update_one(
        {"id": data.kursim_id},
        {"$set": {"depozitimi_history": history, "shuma_aktuale": new_shuma}}
    )
    
    return {"message": "Depozitimi u regjistrua me sukses"}

# ============ BANKA ACCOUNTS ============

@api_router.post("/banka-accounts", response_model=BankaAccount)
async def create_banka_account(data: BankaAccountCreate, current_user: User = Depends(require_admin)):
    banka = BankaAccount(**data.model_dump())
    doc = banka.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.banka_accounts.insert_one(doc)
    return banka

@api_router.get("/banka-accounts", response_model=List[BankaAccount])
async def get_banka_accounts(current_user: User = Depends(require_admin)):
    accounts = await db.banka_accounts.find({}, {"_id": 0}).to_list(10)
    return accounts

@api_router.put("/banka-accounts/{account_id}", response_model=BankaAccount)
async def update_banka_account(account_id: str, data: BankaAccountCreate, current_user: User = Depends(require_admin)):
    await db.banka_accounts.update_one({"id": account_id}, {"$set": data.model_dump()})
    updated = await db.banka_accounts.find_one({"id": account_id}, {"_id": 0})
    return BankaAccount(**updated)

@api_router.delete("/banka-accounts/{account_id}")
async def delete_banka_account(account_id: str, current_user: User = Depends(require_admin)):
    await db.banka_accounts.delete_one({"id": account_id})
    return {"message": "Llogaria bankare u fshi me sukses"}

# ============ KONTABILISTET ============

@api_router.get("/kontabilistet", response_model=List[User])
async def get_kontabilistet(current_user: User = Depends(require_admin)):
    kontabilistet = await db.users.find({"role": "kontabilist"}, {"_id": 0}).to_list(1000)
    return kontabilistet

@api_router.delete("/kontabilistet/{user_id}")
async def delete_kontabilist(user_id: str, current_user: User = Depends(require_admin)):
    await db.users.delete_one({"id": user_id})
    return {"message": "Kontabilisti u fshi me sukses"}

# ============ EXPORT FULL BACKUP ============

@api_router.get("/export/full-backup")
async def export_full_backup(current_user: User = Depends(require_admin)):
    # Collect all data
    data = {
        "borxhe": await db.borxhe.find({}, {"_id": 0}).to_list(10000),
        "shpenzime": await db.shpenzime.find({}, {"_id": 0}).to_list(10000),
        "financa_ditore": await db.financa_ditore.find({}, {"_id": 0}).to_list(10000),
        "stock": await db.stock.find({}, {"_id": 0}).to_list(10000),
        "fatura": await db.fatura.find({}, {"_id": 0}).to_list(10000),
        "deklarimet": await db.deklarimet.find({}, {"_id": 0}).to_list(10000),
        "pagat": await db.pagat.find({}, {"_id": 0}).to_list(10000),
        "crm": await db.crm.find({}, {"_id": 0}).to_list(10000),
        "crm_cpp": await db.crm_cpp.find({}, {"_id": 0}).to_list(10000),
        "kursime": await db.kursime.find({}, {"_id": 0}).to_list(10000),
        "banka_accounts": await db.banka_accounts.find({}, {"_id": 0}).to_list(100),
        "users": await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)
    }
    
    json_data = json.dumps(data, indent=2, default=str)
    
    return StreamingResponse(
        iter([json_data]),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=avalant_backup.json"}
    )

app.include_router(api_router)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "AVALANT Manager"}

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()