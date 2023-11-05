import datetime
from typing import Annotated

from config.config import settings
from database.database import DBSession
from database.models.patient import Patient
from database.models.provider import Provider
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy.orm import Session

provider_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="provider/token")
patient_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="patient/token")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Token(BaseModel):
    access_token: str
    token_type: str

def get_current_provider(token: Annotated[str, Depends(provider_oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.pass_key, algorithms=["HS256"])
        id: str = payload.get("sub")
        if id is None:
            raise credentials_exception
        user: Provider = None
        session: Session
        with DBSession() as session:
            user = session.get(Provider, id)
        if user is None:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception


def get_current_active_provider(
    current_user: Annotated[Provider, Depends(get_current_provider)]
):
    # TODO: add support for disabling providers
    return current_user

def get_current_patient(token: Annotated[str, Depends(patient_oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.pass_key, algorithms=["HS256"])
        id: str = payload.get("sub")
        if id is None:
            raise credentials_exception
        user: Patient = None
        session: Session
        with DBSession() as session:
            user = session.get(Patient, id)
        if user is None:
            raise credentials_exception
        return user
    except JWTError:
        raise credentials_exception


def get_current_active_patient(
    current_user: Annotated[Patient, Depends(get_current_patient)]
):
    # TODO: add support for disabling patients
    return current_user

def create_access_token(data: dict, expires_delta: datetime.timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.datetime.utcnow() + expires_delta
    else:
        expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.pass_key, algorithm="HS256")
    return encoded_jwt

def get_hash(value):
    return pwd_context.hash(value)

def verify_password(password, password_hash):
    return pwd_context.verify(password, password_hash)