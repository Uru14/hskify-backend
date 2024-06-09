from datetime import datetime, timedelta
from typing import List, Any, Generator

from cachetools import TTLCache
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.sql.expression import func
from jose import JWTError, jwt
from database.database import SessionLocal
from database.models import Character, Progress, User, Score
from models import (
    CharacterDetailResponse,
    CharacterFlashcardResponse,
    GameScore,
    HanziSimpleResponse,
    Token,
    UserCreate,
    UserResponse, ExampleSentenceResponse, TokenData,
)
from utils.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
    credentials_exception,
    decode_access_token,
    get_password_hash,
    get_user,
    oauth2_scheme, SECRET_KEY, ALGORITHM,
)
import uvicorn
from contexttimer import Timer
app = FastAPI()

# Configuración de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=['http://localhost:4200'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) -> User:
    token_data = decode_access_token(token)
    user = get_user(db, str(token_data.username))
    if user is None:
        raise credentials_exception
    return user




@app.post('/users/', response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)) -> dict[str, Any]:
    db_user = db.query(User).filter(User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail='Email already registered')
    hashed_password = get_password_hash(user.password)
    db_user = User(email=user.email, name=user.name, password_hash=hashed_password, registration_date=datetime.now())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Una vez creado el usuario en la base de datos, se crea también automáticamente un token para quedar autenticado.
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={'sub': db_user.email}, expires_delta=access_token_expires)
    return {
        'id': db_user.id,
        'email': db_user.email,
        'name': db_user.name,
        'registration_date': db_user.registration_date,
        'access_token': access_token,
        'token_type': 'bearer',
    }


# Se crea un cache que guarda 1 item y expira después de 24h
cache: TTLCache[str, HanziSimpleResponse] = TTLCache(maxsize=1, ttl=timedelta(days=1).total_seconds())


@app.get('/wordDay/', response_model=HanziSimpleResponse)
def get_word_of_day(db: Session = Depends(get_db)) -> Any:
    if 'word_of_day' not in cache:
        word_of_day = (
            db.query(Character).order_by(func.random()).first()
        )  # func.random() ordena todos los registros de manera aleatoria y .first() selecciona el
        # primero de esa lista aleatoria
        if not word_of_day:
            raise HTTPException(status_code=404, detail='No characters found')
        cache['word_of_day'] = HanziSimpleResponse(hanzi=word_of_day.hanzi, pinyin=word_of_day.pinyin)
    return cache['word_of_day']


@app.get('/characters/', response_model=List[CharacterFlashcardResponse])
def get_characters(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)) -> list[Any]:
    characters = (
        db.query(Character.id, Character.hanzi, Character.pinyin, Character.translation).offset(skip).limit(limit).all()
    )
    return characters


@app.get('/characters/all', response_model=List[CharacterFlashcardResponse])
def get_characters_all(db: Session = Depends(get_db)) -> list[Any]:
    characters = db.query(Character.id, Character.hanzi, Character.pinyin, Character.translation).all()
    return characters


@app.get('/characters/{character_id}/', response_model=CharacterDetailResponse)
def get_character_detail(
        character_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
) -> Any:
    with Timer() as timer:
        character = (
            db.query(Character)
            .options(joinedload(Character.example_sentences))
            .filter(Character.id == character_id)
            .first()
        )
    print(timer.elapsed)
    if character is None:
        raise HTTPException(status_code=404, detail='Character not found')

    with Timer() as timer:
        progress_entry = db.query(Progress).filter_by(user_id=current_user.id, character_id=character_id).first()
    print(timer.elapsed)

    return CharacterDetailResponse(
        id=character.id,
        hanzi=character.hanzi,
        pinyin=character.pinyin,
        translation=character.translation,
        stroke_count=character.stroke_count,
        hsk_level=character.hsk_level,
        example_sentences=[
            ExampleSentenceResponse(sentence=sentence.sentence, translation=sentence.translation)
            for sentence in character.example_sentences
        ],

        is_favorite=progress_entry.is_favorite if progress_entry else False,
    )


@app.post('/characters/{character_id}/favorite')
def mark_as_favorite(
        character_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    user_id = current_user.id
    progress_entry = db.query(Progress).filter_by(user_id=user_id, character_id=character_id).first()
    if progress_entry:
        progress_entry.is_favorite = not bool(progress_entry.is_favorite)  # type: ignore[assignment]
        db.commit()
        return {'status': 'Character favorite status updated', 'is_favorite': bool(progress_entry.is_favorite)}
    else:
        new_progress = Progress(
            user_id=user_id, character_id=character_id, is_favorite=True, learning_date=datetime.now()
        )
        db.add(new_progress)
        db.commit()
        return {'status': 'Character marked as favorite and progress created'}


@app.post('/game/{game_id}/score/', response_model=GameScore)
def post_score(game_id: int, score_data: GameScore, db: Session = Depends(get_db), current_user: User = Depends(get_current_user),) -> Any:
    score_entry = Score(game_id=game_id, user_id=current_user.id, score=score_data.score, difficulty=score_data.difficulty, parameters=score_data.parameters)
    db.add(score_entry)
    db.commit()
    db.refresh(score_entry)
    return score_entry


@app.get('/users/favorites', response_model=List[CharacterDetailResponse])
def get_favorites(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)) -> Any:
    favorites = (
        db.query(Character)
        .join(Progress)
        .filter(Progress.user_id == current_user.id, Progress.is_favorite == True)  # noqa: E712
        .all()
    )
    # Convert Character objects to CharacterDetailResponse objects
    response_data = [
        CharacterDetailResponse(
            id=character.id,
            hanzi=character.hanzi,
            pinyin=character.pinyin,
            translation=character.translation,
            stroke_count=character.stroke_count,
            hsk_level=character.hsk_level,
            example_sentences=[],  # Assuming you handle example_sentences elsewhere
            is_favorite=progress.is_favorite  # Access is_favorite from the joined Progress table
        )
        for character, progress in zip(favorites, db.query(Progress).filter(Progress.character_id.in_(f for f in [c.id for c in favorites])))]  # noqa: E712

    return response_data


@app.post('/token', response_model=Token)
def login_for_access_token(
        db: Session = Depends(get_db), form_data: OAuth2PasswordRequestForm = Depends()) -> dict[str, str]:
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={'sub': user.email}, expires_delta=access_token_expires)
    return {'access_token': access_token, 'token_type': 'bearer'}


@app.get('/users/me/', response_model=UserResponse)
def read_users_me(current_user: User = Depends(get_current_user)) -> User:
    return current_user

if __name__ == '__main__':
    uvicorn.run(
        'main:app',
        reload=True,
        host="localhost",
        port=8000,
    )
    
