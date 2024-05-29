from datetime import datetime
from typing import List, Union

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    name: str
    registration_date: datetime

    class Config:
        orm_mode = True


class HanziSimpleResponse(BaseModel):
    hanzi: str
    pinyin: str


class CharacterFlashcardResponse(BaseModel):
    id: int
    hanzi: str
    pinyin: str
    translation: str


class ExampleSentenceResponse(BaseModel):
    sentence: str
    translation: str


class CharacterDetailResponse(BaseModel):
    id: int
    hanzi: str
    pinyin: str
    translation: str
    stroke_count: int
    hsk_level: int
    example_sentences: List[ExampleSentenceResponse]
    is_favorite: bool

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Union[str, None] = None


class Login(BaseModel):
    username: str
    password: str


class GameScore(BaseModel):
    score: int
    difficulty: str
    parameters: str #esto debería ser distinto, pero como solo tengo un juego lo dejo así para pasar el modo de juego