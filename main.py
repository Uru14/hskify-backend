from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from database.database import SessionLocal
from database.models import User, Character
from models import (UserResponse, UserCreate, Token, TokenData, Login, HanziSimpleResponse, CharacterFlashcardResponse,
                    CharacterDetailResponse)
from utils.security import verify_password, create_access_token, get_password_hash
from sqlalchemy.sql.expression import func
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from cachetools import TTLCache
from datetime import timedelta

app = FastAPI()

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


"""
@app.post("/token", response_model=Token)
def login_for_access_token(form_data: Login, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}
"""


@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, name=user.name, password_hash=hashed_password)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


#Se crea un cache que guarda 1 item y expira después de 24h
cache = TTLCache(maxsize=1, ttl=timedelta(days=1).total_seconds())


@app.get("/wordDay/", response_model=HanziSimpleResponse)
def get_word_of_day(db: Session = Depends(get_db)):
    if 'word_of_day' not in cache:
        word_of_day = db.query(Character).order_by(
            func.random()).first()  # func.random() ordena todos los registros de manera aleatoria y .first() selecciona el primero de esa lista aleatoria
        if not word_of_day:
            raise HTTPException(status_code=404, detail="No characters found")
        cache['word_of_day'] = HanziSimpleResponse(hanzi=word_of_day.hanzi, pinyin=word_of_day.pinyin)
    return cache['word_of_day']


@app.get("/characters/", response_model=List[CharacterFlashcardResponse])
def get_characters(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)):
    characters = db.query(Character.id, Character.hanzi, Character.pinyin, Character.translation).offset(skip).limit(limit).all()
    return characters


@app.get("/characters/{character_id}/", response_model=CharacterDetailResponse)
def get_character_detail(character_id: int, db: Session = Depends(get_db)):
    character = db.query(Character).options(joinedload(Character.example_sentences)).filter(
        Character.id == character_id).first()
    if character is None:
        raise HTTPException(status_code=404, detail="Character not found")
    return character
