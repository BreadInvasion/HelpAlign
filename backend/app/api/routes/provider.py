from datetime import timedelta
from typing import Annotated
from uuid import UUID, uuid4

from api.maps import AddressNotValidException, Geocode, ValidationData, validate_address
from database.database import DBSession
from database.models.messaging import (
    ContactMailbox,
    Device,
    DeviceSet,
    Mailbox,
    UserType,
)
from database.models.provider import (
    AcceptingNewPatients,
    Provider,
    ProviderGenderIdentity,
    ProviderType,
)
from database.models.token import ProviderDBToken
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, SecretStr
from security.access import (
    Token,
    create_access_token,
    get_current_active_provider,
    get_hash,
    verify_password,
)
from sqlalchemy import delete, func, select, update
from sqlalchemy.orm import Session


class ProviderLocation(BaseModel):
    street_address: str
    unit: str | None
    city: str
    state_abbreviation: str
    zip_code: str

class ProviderGeocode(BaseModel):
    latitude: float
    longitude: float

class ProviderFilters(BaseModel):
    remote_available: bool
    provider_type: ProviderType
    gender_identity: ProviderGenderIdentity
    accepting_new_patients: AcceptingNewPatients

class NewProviderInfo(BaseModel):
    given_name: str
    family_name: str
    email: EmailStr
    password: SecretStr
    
    location_data: ProviderLocation
    filter_data: ProviderFilters

    #auth info for the requesting device's mailbox
    public_key: str
    signed_pre_key: str

router = APIRouter()

@router.post("/provider/token", response_model=Token)
def provider_login(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    user: Provider | None = None
    session: Session
    with DBSession() as session:
        user = session.scalars(select(Provider).where(Provider.email == form_data.username)).one_or_none()
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
        session.add(ProviderDBToken(user_id=user.id, token_hash=get_hash(access_token)))
        session.commit()

    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/provider/logout")
def patient_logout(token: str, patient: Annotated[Provider, Depends(get_current_active_provider)]):
    session: Session
    with DBSession() as session:
        session.execute(delete(ProviderDBToken).where(ProviderDBToken.token_hash == get_hash(token)).where(ProviderDBToken.user_id == patient.id))
        session.commit()


@router.post("/provider/new")
def create_provider(info: NewProviderInfo):
    session: Session
    with DBSession() as session:
        if session.scalars(select(Provider).where(Provider.email == info.email)).one_or_none():
            raise HTTPException(status_code=409, detail="Provider already registered with this email")

    # Validate and format address
    location_data: ValidationData
    try:
        location_data = validate_address(info.location_data.street_address, info.location_data.city, info.location_data.state_abbreviation, info.location_data.zip_code, info.location_data.unit)
    except AddressNotValidException:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="BAD FIELD: ADDRESS")

    password_hash = get_hash(info.password.get_secret_value())

    session: Session
    with DBSession() as session:
        session.add(Provider(
                            device_set=DeviceSet(
                                                user_type=UserType.PROVIDER, 
                                                devices=[
                                                        Device(
                                                                identity_public_key=info.public_key, 
                                                                signed_pre_key=info.signed_pre_key, 
                                                                mailbox=Mailbox(messages=[]),
                                                                contact_mailbox=ContactMailbox(messages=[])
                                                            )
                                                        ]
                                                ),
                            given_name=info.given_name, 
                            family_name=info.family_name, 
                            email=info.email, 
                            formatted_address=location_data.formatted_address,
                            latitude=location_data.geocode.latitude,
                            longitude=location_data.geocode.longitude, 
                            state_abbreviation=location_data.state_abbreviation,
                            remote_available=info.filter_data.remote_available, 
                            gender_identity=info.filter_data.gender_identity, 
                            accepting_new_patients=info.filter_data.accepting_new_patients,
                            provider_type=info.filter_data.provider_type,
                            password_hash=password_hash,
                        )
                    )
        
        session.commit()

    return {"success": True}

@router.post("/provider/changeemail")
def change_email(new_email: EmailStr, user: Annotated[Provider, Depends(get_current_active_provider)]):
    session: Session
    with DBSession() as session:
        if session.scalars(select(Provider).where(Provider.email == new_email)).one_or_none():
            raise HTTPException(status_code=409, detail="Provider already registered with this email")
        
        session.execute(update(Provider), [{"id": user.id, "email": new_email}])
        session.commit()
    
    return {"success": True}

@router.post("/provider/delete")
def delete_provider(provider_id: UUID, passkey: str):
    if passkey != "thiswillbeproperlysecuredeventually":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)
    
    session: Session
    with DBSession() as session:
        session.execute(delete(Provider).where(Provider.id==provider_id))
        session.commit()

    return {"succeeded": True}