# app.py - ¡LA VERSIÓN DE VICTORIA FINAL CON FASTAPI!

import os
import json
import time
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from datetime import datetime, timedelta, timezone
import jwt
from pydantic import BaseModel
import google.generativeai as genai
import bcrypt
from logic import get_post_details

# Importamos nuestras clases y funciones
from models import Base, User, Analysis, Strategy
from logic import scrape_instagram_comments, analyze_comments_with_ai, find_instagram_posts_by_hashtag, generate_prospecting_strategy

# --- CONFIGURACIÓN ---
DATABASE_URL = "sqlite:///./setter_mind.db"
SECRET_KEY = "clave-secreta-para-jwt-12345"
ALGORITHM = "HS256"

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)

# Configuración de Gemini
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY_PLANTILLA')
genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('models/gemini-pro-latest')

# --- Modelos Pydantic (DTOs) ---
class UserCreate(BaseModel): username: str; email: str; password: str
class UserLogin(BaseModel): email: str; password: str
class ProspectRequest(BaseModel): hashtag: str
class AnalyzeRequest(BaseModel): post_url: str; niche: str; avatar: str
# ... debajo de los otros modelos Pydantic ...
class StrategyRequest(BaseModel):
    niche: str
    avatar: str
class PostDetailsRequest(BaseModel):
    post_url: str

# --- Dependencias y Lógica de Auth ---
def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

from fastapi.security import OAuth2PasswordBearer
from pydantic import ValidationError

# Creamos el "esquema" que le dice a FastAPI que busque el token en la cabecera "Authorization"
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    """
    Dependencia para obtener el usuario actual a partir del token JWT.
    Este es nuestro nuevo "guardia de seguridad".
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except (jwt.PyJWTError, ValidationError):
        raise credentials_exception
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user

# --- ¡NUESTRAS FUNCIONES DE CONFIANZA! ---
def verify_password(plain_password, hashed_password):
    # Truncamos la contraseña que nos envía el usuario antes de verificarla
    return bcrypt.checkpw(plain_password.encode('utf-8')[:72], hashed_password.encode('utf-8'))

def get_password_hash(password):
    # Truncamos la contraseña a 72 bytes
    p_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(p_bytes, salt).decode('utf-8')
def create_access_token(data: dict):
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode = data.copy(); to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

# --- API Endpoints ---
@app.get("/")
def read_root(): return {"message": "SetterMind AI con FastAPI ¡VICTORIA FINAL!"}

@app.post("/api/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=409, detail="El email ya está registrado.")
    hashed_password = get_password_hash(user.password)
    new_user = User(username=user.username, email=user.email, hashed_password=hashed_password)
    db.add(new_user); db.commit()
    return {"message": "Usuario registrado exitosamente."}

@app.post("/api/login")
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if not db_user or not verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Credenciales inválidas.")
    access_token = create_access_token(data={"sub": db_user.id})
    return {"token": access_token}

@app.post("/api/prospect")
def prospect_posts(req: ProspectRequest):
    posts = find_instagram_posts_by_hashtag(req.hashtag)
    if posts is None: raise HTTPException(status_code=500, detail="La búsqueda de prospectos falló.")
    return {"found_posts": posts}

@app.post("/api/analyze")
def analyze_post(req: AnalyzeRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Obtenemos los detalles del post, incluyendo el caption.
    post_details = get_post_details(req.post_url, gemini_model)
    if not post_details:
        raise HTTPException(status_code=404, detail="No se pudieron obtener los detalles del post para el contexto.")

    comments = scrape_instagram_comments(req.post_url)
    if not comments: raise HTTPException(status_code=404, detail="No se encontraron comentarios.")
    
    # --- ¡CONTEXTO MEJORADO! ---
    context = {
        "niche": req.niche, 
        "avatar": req.avatar,
        "caption": post_details.get('caption') # ¡Añadimos el caption!
    }
    
    ai_analysis_json_string = analyze_comments_with_ai(comments, context, gemini_model)
    if not ai_analysis_json_string: raise HTTPException(status_code=500, detail="Análisis de IA falló.")
    
    try:
        ai_results = json.loads(ai_analysis_json_string)
        ai_results['summary'] = f"Analizados {len(comments)} com., IA identificó {len(ai_results.get('leads', []))} prospectos."
        
        # --- ¡LÓGICA DE GUARDADO ACTIVADA! ---
        # Usamos el 'current_user' que nos da nuestro guardia de seguridad.
        new_analysis = Analysis(
            post_url=req.post_url, 
            result_data=ai_results, 
            owner_id=current_user.id # Conectamos el análisis al usuario
        )
        db.add(new_analysis)
        db.commit()
        print(f"Análisis para el usuario {current_user.username} guardado en la DB.")
        
        return ai_results
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Respuesta de IA no es JSON válido.")

@app.get("/api/history")
def get_analysis_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # --- ¡LÓGICA REAL DE CONSULTA! ---
    # Buscamos en la tabla Analysis, filtramos por el ID del usuario y ordenamos.
    user_analyses = db.query(Analysis).filter(Analysis.owner_id == current_user.id).order_by(Analysis.created_at.desc()).all()
    
    # Convertimos los resultados a un formato JSON.
    history_list = [
        {
            'id': analysis.id,
            'post_url': analysis.post_url,
            'created_at': analysis.created_at.isoformat(),
            'summary': analysis.result_data.get('summary', 'Sin resumen.')
        } for analysis in user_analyses
    ]
    
    return {"history": history_list}

@app.get("/api/strategies")
def get_strategies(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_strategies = db.query(Strategy).filter(Strategy.owner_id == current_user.id).order_by(Strategy.created_at.desc()).all()
    
    return user_strategies # FastAPI convierte automáticamente los modelos de SQLAlchemy a JSON

@app.post("/api/generate-strategy")
# --- ¡MODIFICADO! Añadimos la dependencia del usuario y la DB ---
def generate_strategy(req: StrategyRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    context = {"niche": req.niche, "avatar": req.avatar}
    strategy_json_string = generate_prospecting_strategy(context, gemini_model)
    
    if not strategy_json_string:
        raise HTTPException(status_code=500, detail="La generación de estrategia falló.")
        
    try:
        strategy_data = json.loads(strategy_json_string)
        
        # --- ¡NUEVA LÓGICA DE GUARDADO! ---
        new_strategy = Strategy(
            niche=req.niche,
            avatar=req.avatar,
            keywords=strategy_data.get('keywords', []),
            hashtags=strategy_data.get('hashtags', []),
            owner_id=current_user.id
        )
        db.add(new_strategy)
        db.commit()
        print(f"Estrategia para el usuario {current_user.username} guardada en la DB.")
        
        return strategy_data
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="La respuesta de la IA (estrategia) no es un JSON válido.")

@app.post("/api/get-post-details")
def fetch_post_details(req: PostDetailsRequest, current_user: User = Depends(get_current_user)):
    details = get_post_details(req.post_url, gemini_model)
    if not details:
        raise HTTPException(status_code=404, detail="No se pudieron obtener los detalles del post.")
    return details

# --- LÓGICA PARA CORRER EL SERVIDOR (si se ejecuta directamente) ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5001, reload=True)