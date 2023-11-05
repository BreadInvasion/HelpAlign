from datetime import timedelta
from typing import Annotated
from uuid import UUID

from database.database import DBSession
from database.models.messaging import Device, DeviceSet, Mailbox, UserType
from database.models.patient import Patient
from database.models.token import PatientDBToken
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, SecretStr
from security.access import (
    create_access_token,
    get_current_active_patient,
    get_hash,
    verify_password,
)
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

router = APIRouter()

@router.post("/patient/token")
def patient_login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user: Patient | None
    session: Session
    with DBSession() as session:
        user = session.scalars(select(Patient).where(Patient.email == form_data.username)).one_or_none()
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    if not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Incorrect username or password")

    access_token_expires = timedelta(minutes=30)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )

    session: Session
    with DBSession() as session:
        session.add(PatientDBToken(user_id=user.id, token_hash=get_hash(access_token)))
        session.commit()

    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/patient/logout")
def patient_logout(token: str, patient: Annotated[Patient, Depends(get_current_active_patient)]):
    session: Session
    with DBSession() as session:
        session.execute(delete(PatientDBToken).where(PatientDBToken.token == token).where(PatientDBToken.user_id == patient.id))
        session.commit()

class Name(BaseModel):
    given: str
    family: str

class PatientAssistanceInfo(BaseModel):
    is_assisted_account: bool
    guardian_name: Name | None

class NewPatientInfo(BaseModel):
    email: EmailStr
    password: SecretStr
    assistance: PatientAssistanceInfo
    name: Name

    public_key: str
    signed_pre_key: str

@router.post("/patient/new")
def create_patient(info: NewPatientInfo):
    session: Session
    with DBSession() as session:
        if session.scalars(select(Patient).where(Patient.email == info.email)).one_or_none():
            raise HTTPException(status_code=409, detail="Provider already registered with this email")

    if info.assistance.is_assisted_account and not info.assistance.guardian_name:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="ASSISTED ACCOUNTS REQUIRE GUARDIAN NAME")

    password_hash = get_hash(info.password.get_secret_value())

    session: Session
    with DBSession() as session:
        session.add(Patient(
                            device_set=DeviceSet(
                                                user_type=UserType.PATIENT, 
                                                devices=[
                                                        Device(
                                                                identity_public_key=info.public_key, 
                                                                signed_pre_key=info.signed_pre_key, 
                                                                mailbox=Mailbox(messages=[])
                                                            )
                                                        ]
                                                ),
                            given_name=info.name.given, 
                            family_name=info.name.family, 
                            email=info.email,
                            password_hash=password_hash,
                            is_assisted_account=info.assistance.is_assisted_account,
                            guardian_given_name=info.assistance.guardian_name.given if info.assistance.guardian_name else None,
                            guardian_family_name=info.assistance.guardian_name.family if info.assistance.guardian_name else None,
                        )
                    )
        
        session.commit()

    return {"success": True}

@router.post("/patient/delete")
def delete_patient(patient_id: UUID, passkey: str):
    if passkey != "thiswillbeproperlysecuredeventually":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    session: Session
    with DBSession() as session:
        session.execute(delete(Patient).where(Patient.id==patient_id))
        session.commit()

    return {"succeeded": True}