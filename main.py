from fastapi import FastAPI, Depends, HTTPException, status, Request
from sqlalchemy.orm import Session, joinedload
from database.database import SessionLocal
from database.models import User, Character, Progress
from models import (UserResponse, UserCreate, Token, TokenData, Login, HanziSimpleResponse, CharacterFlashcardResponse,
                    CharacterDetailResponse)
from utils.security import verify_password, create_access_token, get_password_hash, oauth2_scheme, authenticate_user, \
    decode_access_token, ACCESS_TOKEN_EXPIRE_MINUTES, get_user, credentials_exception
from sqlalchemy.sql.expression import func
from typing import List, Annotated, Union
from fastapi.middleware.cors import CORSMiddleware
from cachetools import TTLCache
from datetime import timedelta
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging
from datetime import datetime

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

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)):
    token_data = decode_access_token(token)
    user = get_user(db, token_data.username)
    if user is None:
        raise credentials_exception
    return user

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    exc_str = f'{exc}'.replace('\n', ' ').replace('   ', ' ')
    logging.error(f"{request}: {exc_str}")
    content = {'status_code': 10422, 'message': exc_str, 'data': None}
    return JSONResponse(content=content, status_code=status.HTTP_422_UNPROCESSABLE_ENTITY)

@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, name=user.name, password_hash=hashed_password, registration_date=datetime.now())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Una vez creado el usuario en la base de datos, se crea también automáticamente un token para quedar autenticado.
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": db_user.email}, expires_delta=access_token_expires
    )
    return {
        "id": db_user.id,
        "email": db_user.email,
        "name": db_user.name,
        "registration_date": db_user.registration_date,
        "access_token": access_token,
        "token_type": "bearer"
    }


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
    characters = db.query(Character.id, Character.hanzi, Character.pinyin, Character.translation).offset(skip).limit(
        limit).all()
    return characters


@app.get("/characters/all", response_model=List[CharacterFlashcardResponse])
def get_characters(db: Session = Depends(get_db)):
    characters = db.query(Character.id, Character.hanzi, Character.pinyin, Character.translation).all()
    return characters


@app.get("/characters/{character_id}/", response_model=CharacterDetailResponse)
def get_character_detail(character_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    character = db.query(Character).options(joinedload(Character.example_sentences)).filter(
        Character.id == character_id).first()
    if character is None:
        raise HTTPException(status_code=404, detail="Character not found")

    progress_entry = db.query(Progress).filter_by(
        user_id=current_user.id, character_id=character_id
    ).first()

    if progress_entry:
        character.isFavorite = progress_entry.is_favorite
    else:
        character.isFavorite = False
    return character


@app.post("/characters/{character_id}/favorite")
def mark_as_favorite(character_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_id = current_user.id
    progress_entry = db.query(Progress).filter_by(user_id=user_id, character_id=character_id).first()
    if progress_entry:
        progress_entry.is_favorite = not progress_entry.is_favorite
        db.commit()
        return {"status": "Character favorite status updated", "is_favorite": progress_entry.is_favorite}
    else:
        new_progress = Progress(user_id=user_id, character_id=character_id, is_favorite=True, learning_date=datetime.now())
        db.add(new_progress)
        db.commit()
        return {"status": "Character marked as favorite and progress created"}


@app.get("/users/{user_id}/favorites", response_model=List[CharacterFlashcardResponse])
def get_favorites(user_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_id = current_user.id
    favorites = db.query(Character).join(Progress).filter(Progress.user_id == user_id,
                                                          Progress.is_favorite == True).all()
    return favorites


@app.post("/token", response_model=Token)
def login_for_access_token(db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/users/me/", response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user


