from datetime import datetime, timedelta, timezone
from typing import Union, Any

from fastapi import HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext

from database.models import User
from models import TokenData

# openssl rand -hex 32
SECRET_KEY = '94c5a69806421a64c9f61722973f48782ea4d456389bee2e556c91507c27b709'
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_DAYS = 30

pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='token')

credentials_exception = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail='Could not validate credentials',
    headers={'WWW-Authenticate': 'Bearer'},
)


def create_access_token(data: dict[str, Any], expires_delta: Union[timedelta, None] = None) -> str:
    """
    Creates a JSON Web Token (JWT) with the provided data and optional expiration delta.
    If expires_delta is provided, sets the token expiration based on current UTC time.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=30)
    to_encode.update({'exp': expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies if the plain password matches the hashed password securely stored in the database.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> bool:
    """
    Hashes the provided password securely using the specified hashing algorithm (bcrypt).
    """
    return pwd_context.hash(password)


def get_user(db: Session, username: str) -> User | None:
    """
    Retrieves a user from the database based on the provided username (email).
    Returns None if no user with that username exists.
    """
    user = db.query(User).filter(User.email == username).first()
    return user


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    """
    Authenticates a user by verifying their username (email) and password.
    Returns the User object if authentication is successful, otherwise returns None.
    """
    user = get_user(db, username)
    if not user:
        return None
    if not verify_password(password, str(user.password_hash)):
        return None
    return user


def decode_access_token(token: str) -> TokenData:
    """
    Decodes and verifies the JWT token to extract the token data.
    Raises HTTPException if the token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError as exc:
        raise credentials_exception from exc
    return token_data
