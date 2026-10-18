import sys
import os
import uuid
import bcrypt
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import User, Base

db_url = os.environ.get("DATABASE_URL", "sqlite:///./setter_mind.db")
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(db_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8')[:72], bcrypt.gensalt()).decode('utf-8')

def set_user(email, username, password, plan_tier="basic"):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.username = username
            user.plan_tier = plan_tier.lower()
            if password:
                user.hashed_password = get_password_hash(password)
            db.commit()
            print(f"✓ Usuario '{email}' actualizado. Plan: {user.plan_tier}")
        else:
            hashed = get_password_hash(password)
            new_u = User(
                id=str(uuid.uuid4()),
                email=email,
                username=username,
                hashed_password=hashed,
                plan_tier=plan_tier.lower(),
                monthly_generations_count=0
            )
            db.add(new_u)
            db.commit()
            print(f"✓ Usuario '{email}' creado exitosamente. Plan: {plan_tier.lower()}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Uso: python manage_users.py <email> <username> <password> [basic|pro|plus]")
        sys.exit(1)
    
    tier = sys.argv[4] if len(sys.argv) > 4 else "basic"
    set_user(sys.argv[1], sys.argv[2], sys.argv[3], tier)
