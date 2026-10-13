# app.py
import os
import json
import hashlib
import secrets
from fastapi import FastAPI, Depends, HTTPException, status, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta, timezone
import jwt
from pydantic import BaseModel
from typing import Any, Optional
import bcrypt
from mailer import send_welcome_email

# Modelos y Lógica
from models import Base, User, ApiKey, Analysis, Strategy, OutboxItem, Conversation
from logic import (
    scrape_instagram_comments,
    analyze_comments_with_ai,
    find_instagram_posts_by_hashtag,
    generate_prospecting_strategy,
    get_post_details,
    generate_highlights_logic,
    generate_content_ideas_logic,
    generate_lead_magnet_logic,
    generate_engagement_poll_logic,
    generate_profile_magnet_logic,
)

# --- CONFIGURACIÓN DE ENTORNO ---
DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./setter_mind.db")
# Compatibilidad para URLs de Postgres en Render (postgres:// -> postgresql://)
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "clave-secreta-para-jwt-12345")
HOTTOK_SECRET = os.environ.get("HOTTOK_SECRET", "qOLPyTTtTuN3fMvdqra2zZ5vkz738m90495356")
ALGORITHM = "HS256"

app = FastAPI(title="SetterMind AI API")
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://settermind.mentesalmercado.online",
        "http://localhost:3000",
        "*"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- MODELOS PYDANTIC ---
class UserCreate(BaseModel): username: str; email: str; password: str
class UserLogin(BaseModel): email: str; password: str
class ProspectRequest(BaseModel): hashtag: str
class AnalyzeRequest(BaseModel):
    post_url: str
    niche: str = "General"
    avatar: str = "Audiencia interesada"
class StrategyRequest(BaseModel): niche: str; avatar: str
class PostDetailsRequest(BaseModel): post_url: str
class OutboxCreate(BaseModel):
    post_url: str
    prospect_username: str
    prospect_comment: str
    selected_opener: str
    identified_pain: str = ''
    score: str | int | float = ''
class StrategyCreate(BaseModel):
    niche: str
    avatar: str
    keywords: list[str] = []
    hashtags: list[str] = []
class ConversationCreate(BaseModel): lead_data: dict[str, Any]
class ConversationUpdate(BaseModel):
    notes: Optional[str] = None
    status: Optional[str] = None

class HighlightsRequest(BaseModel):
    name: str
    mission: str
    method_name: str
    result_example: str

class ContentIdeasRequest(BaseModel):
    topic: str

class LeadMagnetRequest(BaseModel):
    resource_type: str

class EngagementPollRequest(BaseModel):
    question: str

class ProfileMagnetRequest(BaseModel):
    niche: str
    transformation: str
    lead_magnet: Optional[str] = ""

# --- CRIPTOGRAFÍA & AUTH DUAL (JWT + SHA-256 API KEY) ---
def hash_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.strip().encode('utf-8')).hexdigest()

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8')[:72], hashed_password.encode('utf-8'))

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8')[:72], bcrypt.gensalt()).decode('utf-8')

def create_access_token(data: dict) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode = data.copy()
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(
    request: Request,
    authorization: Optional[str] = Header(None),
    x_api_key: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Middleware dual SaaS-20:
    1. Si recibe 'x-api-key', calcula el hash SHA-256 y verifica cuota/estado.
    2. Si recibe 'Authorization: Bearer <token>', valida la sesión JWT.
    """
    # 1. Validación por API Key (Hotmart / Magic Link)
    if x_api_key:
        hashed = hash_api_key(x_api_key)
        api_key_record = db.query(ApiKey).filter(ApiKey.key_hash == hashed).first()
        if not api_key_record or not api_key_record.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API Key inválida o inactiva."
            )
        if api_key_record.current_usage >= api_key_record.monthly_limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Límite mensual de consultas excedido."
            )
        # Incremento de uso atómico
        api_key_record.current_usage += 1
        db.commit()
        return api_key_record.owner

    # 2. Validación tradicional por JWT
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split(" ")[1]
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str = payload.get("sub")
            if user_id is None:
                raise HTTPException(status_code=401, detail="Token no contiene identificador de usuario")
            user = db.query(User).filter(User.id == user_id).first()
            if user is None:
                raise HTTPException(status_code=401, detail="Usuario no encontrado")
            return user
        except jwt.PyJWTError:
            raise HTTPException(status_code=401, detail="Token JWT inválido o expirado")

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Credenciales no proporcionadas (se requiere x-api-key o Bearer token)"
    )

# --- WEBHOOK DE HOTMART (AUTOMATIZACIÓN POST-COMPRA) ---
@app.post("/hotmartWebhook")
async def hotmart_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.json()
    
    # 1. Validar el secreto de Hotmart (Hottok)
    token_received = request.headers.get("hottok") or payload.get("hottok")
    if token_received != HOTTOK_SECRET:
        raise HTTPException(status_code=401, detail="Acceso no autorizado: Hottok inválido")

    event = payload.get("event")
    data = payload.get("data", {})
    buyer = data.get("buyer", {})
    buyer_email = buyer.get("email")

    if not buyer_email:
        return {"status": "ignored", "reason": "No buyer email provided"}

    # 2. EVENTO: COMPRA APROBADA
    if event in ["PURCHASE_APPROVED", "ORDER_APPROVED"]:
        buyer_name = buyer.get("name", buyer_email.split("@")[0])
        
        # Buscar si el usuario ya existe o crearlo
        user = db.query(User).filter(User.email == buyer_email).first()
        if not user:
            user = User(
                username=buyer_name,
                email=buyer_email,
                hashed_password=get_password_hash(secrets.token_hex(12))
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        # Generar la API Key en texto plano para el usuario
        raw_key = f"sk_live_{secrets.token_hex(24)}"
        # Hashear la clave en SHA-256 para guardarla segura en la BD
        hashed_key = hash_api_key(raw_key)

        # ==============================================================
        # AQUÍ ES DONDE SE CREA new_license EN LA BASE DE DATOS:
        # ==============================================================
        new_license = ApiKey(
            key_hash=hashed_key,
            user_email=buyer_email,
            is_active=True,
            monthly_limit=1000,
            owner_id=user.id
        )
        db.add(new_license)
        db.commit()   # <-- Guardado confirmado en base de datos
        print(f"[HOTMART] Licencia creada en BD para {buyer_email}. Key: {raw_key}")

        # ==============================================================
        # JUSTO AQUÍ DESPUÉS SE DISPARA EL CORREO CON RESEND:
        # ==============================================================
        send_welcome_email(
            to_email=buyer_email,
            buyer_name=buyer_name,
            raw_api_key=raw_key
        )

        return {"status": "provisioned", "user_email": buyer_email}

    # 3. EVENTO: REEMBOLSO O CANCELACIÓN
    elif event in ["PURCHASE_REFUNDED", "REFUNDED", "SUBSCRIPTION_CANCELED"]:
        licenses = db.query(ApiKey).filter(ApiKey.user_email == buyer_email).all()
        for lic in licenses:
            lic.is_active = False
        db.commit()
        print(f"[HOTMART] Licencias revocadas para {buyer_email}")
        return {"status": "revoked", "user_email": buyer_email}

    return {"status": "received", "event": event}

# --- RESTO DE ENDPOINTS ---
@app.get("/")
def read_root():
    return {"message": "SetterMind AI API Online", "framework": "FastAPI", "version": "2.0"}

@app.post("/api/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=409, detail="El email ya está registrado.")
    hashed_password = get_password_hash(user.password)
    new_user = User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(new_user)
    db.commit()
    return {"message": "Usuario registrado exitosamente."}

@app.post("/api/login")
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas.")
    access_token = create_access_token(data={"sub": db_user.id})
    return {"token": access_token}

@app.post("/api/prospect")
def prospect_posts(req: ProspectRequest, current_user: User = Depends(get_current_user)):
    posts = find_instagram_posts_by_hashtag(req.hashtag)
    if posts is None:
        raise HTTPException(status_code=500, detail="La búsqueda de prospectos falló.")
    return {"found_posts": posts}

@app.post("/api/analyze-post")
def analyze_post(req: AnalyzeRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    post_details = get_post_details(req.post_url)
    if not post_details:
        raise HTTPException(status_code=404, detail="No se pudieron obtener los detalles del post.")

    comments = scrape_instagram_comments(req.post_url)
    if not comments:
        raise HTTPException(status_code=404, detail="No se encontraron comentarios.")
    post_caption = ""
    if isinstance(post_details, dict):
        post_caption = post_details.get('caption') or (post_details.get('post', {})).get('caption', '')
    context = {
        "niche": req.niche,
        "avatar": req.avatar,
        "caption": post_caption
    }

    ai_analysis_json_string = analyze_comments_with_ai(comments, context)
    if not ai_analysis_json_string:
        raise HTTPException(status_code=500, detail="Análisis de IA falló.")

    try:
        ai_results = json.loads(ai_analysis_json_string)
        ai_results['summary'] = f"Analizados {len(comments)} com., IA identificó {len(ai_results.get('leads', []))} prospectos."
        
        new_analysis = Analysis(
            post_url=req.post_url,
            result_data=ai_results,
            owner_id=current_user.id
        )
        db.add(new_analysis)
        db.commit()

        ai_results["id"] = new_analysis.id
        ai_results["analysis_id"] = new_analysis.id
        return ai_results
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Respuesta de IA no es JSON válido.")
# Al final de analyze_post en app.py:
    return {
        "analysis_id": new_analysis.id,
        "id": new_analysis.id,
        "summary": ai_results.get('summary', ''),
        "leads": ai_results.get('leads', []),
        "comments": comments,  # <--- RETORNAR LOS COMENTARIOS SCRAPEADOS
        "post_details": post_details,
    }

@app.get("/api/analysis/{analysis_id}")
def get_analysis(analysis_id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    analysis = db.query(Analysis).filter(Analysis.id == analysis_id, Analysis.owner_id == current_user.id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Análisis no encontrado.")
    return {**analysis.result_data, "id": analysis.id, "status": "completed"}

@app.get("/api/history")
def get_analysis_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_analyses = db.query(Analysis).filter(Analysis.owner_id == current_user.id).order_by(Analysis.created_at.desc()).all()
    return {"history": [
        {'id': a.id, 'post_url': a.post_url, 'created_at': a.created_at.isoformat(), 'summary': a.result_data.get('summary', '')}
        for a in user_analyses
    ]}

@app.get("/api/strategies")
def get_user_strategies(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    strats = db.query(Strategy).filter(Strategy.owner_id == current_user.id).order_by(Strategy.created_at.desc()).all()
    results = []
    for s in strats:
        results.append({
            "id": s.id,
            "niche": s.niche,
            "avatar": s.avatar,
            "keywords": s.keywords or [],
            "hashtags": s.hashtags or [],
            "saved_posts": s.saved_posts or [],
            "created_at": s.created_at.isoformat() if s.created_at else None
        })
    return {"strategies": results}

@app.post("/api/generate-strategy")
def generate_strategy(req: StrategyRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    context = {"niche": req.niche, "avatar": req.avatar}
    strategy_result = generate_prospecting_strategy(context)
    
    if not strategy_result:
        raise HTTPException(status_code=500, detail="Generación de estrategia falló en OpenAI.")
    
    # Manejar si devuelve un dict o si devuelve un string JSON
    if isinstance(strategy_result, dict):
        strategy_data = strategy_result
    elif isinstance(strategy_result, str):
        try:
            strategy_data = json.loads(strategy_result)
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Respuesta no es JSON válido.")
    else:
        raise HTTPException(status_code=500, detail="Formato de respuesta desconocido.")

    try:
        new_strategy = Strategy(
            niche=req.niche,
            avatar=req.avatar,
            keywords=strategy_data.get('keywords', []),
            hashtags=strategy_data.get('hashtags', []),
            owner_id=current_user.id
        )
        db.add(new_strategy)
        db.commit()
        db.refresh(new_strategy)
        
        # Adjuntamos el ID de la estrategia para poder guardar posts en ella luego
        strategy_data['strategy_id'] = new_strategy.id
        return strategy_data
    except Exception as e:
        db.rollback()
        print(f"Error al persistir estrategia en BD: {e}")
        # Retornamos los datos generados aunque falle el guardado en base de datos
        return strategy_data

@app.post("/api/get-post-details")
def fetch_post_details(req: PostDetailsRequest, current_user: User = Depends(get_current_user)):
    details = get_post_details(req.post_url)
    if not details:
        raise HTTPException(status_code=404, detail="No se pudieron obtener detalles.")
    return details

@app.get("/api/outbox")
def list_outbox(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(OutboxItem).filter_by(owner_id=current_user.id, status='pending').order_by(OutboxItem.created_at.desc()).all()
    return [{
        "id": r.id, "post_url": r.post_url, "prospect_username": r.prospect_username,
        "prospect_comment": r.prospect_comment, "selected_opener": r.selected_opener,
        "identified_pain": r.identified_pain, "score": r.score
    } for r in rows]

@app.post("/api/outbox", status_code=201)
def add_outbox(req: OutboxCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = OutboxItem(**req.model_dump(), owner_id=current_user.id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@app.patch("/api/outbox/{item_id}/sent")
def mark_sent(item_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    item = db.query(OutboxItem).filter_by(id=item_id, owner_id=current_user.id).first()
    if not item:
        raise HTTPException(status_code=404, detail="No encontrado.")
    item.status = 'sent'
    db.add(Conversation(owner_id=current_user.id, status='iniciado', lead_data={
        "username": item.prospect_username, "comment": item.prospect_comment,
        "pain_point": item.identified_pain, "score": item.score,
        "opener": item.selected_opener, "post_url": item.post_url
    }))
    db.commit()
    return {"ok": True}

@app.get("/api/conversations")
def list_conversations(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.query(Conversation).filter_by(owner_id=current_user.id).order_by(Conversation.created_at.desc()).all()
    return [{"id": r.id, "lead_data": r.lead_data, "status": r.status, "notes": r.notes or "", "exported": r.exported} for r in rows]

@app.post("/api/conversations", status_code=201)
def create_conversation(req: ConversationCreate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    conversation = Conversation(owner_id=current_user.id, lead_data=req.lead_data)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation

@app.patch("/api/conversations/{convo_id}")
def update_conversation(convo_id: str, req: ConversationUpdate, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    convo = db.query(Conversation).filter_by(id=convo_id, owner_id=current_user.id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="No encontrado.")
    if req.notes is not None: convo.notes = req.notes
    if req.status is not None: convo.status = req.status
    db.commit()
    return convo

@app.post("/api/conversations/{convo_id}/export")
def export_conversation(convo_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    convo = db.query(Conversation).filter_by(id=convo_id, owner_id=current_user.id).first()
    if not convo:
        raise HTTPException(status_code=404, detail="No encontrado.")
    convo.exported = True
    db.commit()
    return convo

@app.post("/api/generate-highlights")
def api_generate_highlights(req: HighlightsRequest, current_user: User = Depends(get_current_user)):
    res = generate_highlights_logic(req.name, req.mission, req.method_name, req.result_example)
    if not res:
        raise HTTPException(status_code=500, detail="Error al generar highlights.")
    return {"result": res if isinstance(res, str) else json.dumps(res, indent=2, ensure_ascii=False)}

@app.post("/api/generate-content-ideas")
def api_generate_content_ideas(req: ContentIdeasRequest, current_user: User = Depends(get_current_user)):
    res = generate_content_ideas_logic(req.topic)
    if not res:
        raise HTTPException(status_code=500, detail="Error al generar ideas.")
    return {"result": res if isinstance(res, str) else json.dumps(res, indent=2, ensure_ascii=False)}

@app.post("/api/generate-lead-magnet-plan")
def api_generate_lead_magnet(req: LeadMagnetRequest, current_user: User = Depends(get_current_user)):
    res = generate_lead_magnet_logic(req.resource_type)
    if not res:
        raise HTTPException(status_code=500, detail="Error al generar el recurso.")
    return {"result": res if isinstance(res, str) else json.dumps(res, indent=2, ensure_ascii=False)}

@app.post("/api/generate-engagement-poll")
def api_generate_engagement(req: EngagementPollRequest, current_user: User = Depends(get_current_user)):
    res = generate_engagement_poll_logic(req.question)
    if not res:
        raise HTTPException(status_code=500, detail="Error al generar dinámica.")
    return {"result": res if isinstance(res, str) else json.dumps(res, indent=2, ensure_ascii=False)}

@app.post("/api/generate-profile-magnet")
def api_generate_profile_magnet(req: ProfileMagnetRequest, current_user: User = Depends(get_current_user)):
    res = generate_profile_magnet_logic(req.niche, req.transformation, req.lead_magnet)
    if not res:
        raise HTTPException(status_code=500, detail="Error al optimizar perfil.")
    try:
        data = json.loads(res) if isinstance(res, str) else res
        return data
    except Exception:
        return {"bio": str(res), "cta": "Envía un mensaje privado para más detalles."}

@app.post("/api/strategies")
def create_strategy(
    strategy_data: StrategyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        new_strategy = Strategy(
            niche=strategy_data.niche,
            avatar=strategy_data.avatar,
            keywords=strategy_data.keywords,
            hashtags=strategy_data.hashtags,
            owner_id=current_user.id
        )
        db.add(new_strategy)
        db.commit()
        db.refresh(new_strategy)
        return {"status": "success", "strategy_id": new_strategy.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Error al guardar estrategia: {str(e)}")

class AddPostToStrategy(BaseModel):
    url: str
    caption: str = ''
    likesCount: int = 0
    commentsCount: int = 0
    ownerUsername: str = ''

@app.post("/api/strategies/{strategy_id}/posts")
def add_post_to_strategy(
    strategy_id: str,
    post_item: AddPostToStrategy,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    strat = db.query(Strategy).filter(Strategy.id == strategy_id, Strategy.owner_id == current_user.id).first()
    if not strat:
        raise HTTPException(status_code=404, detail="Estrategia no encontrada")

    current_posts = list(strat.saved_posts or [])
    # Evitar duplicados por URL
    if not any(p.get("url") == post_item.url for p in current_posts):
        current_posts.append(post_item.dict())
        strat.saved_posts = current_posts
        db.commit()
        db.refresh(strat)

    return {"status": "success", "saved_posts": strat.saved_posts}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8001)))