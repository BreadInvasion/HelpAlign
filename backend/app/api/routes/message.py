from datetime import datetime
from typing import Annotated, List
from uuid import UUID

from database.database import DBSession
from database.models.messaging import ContactMailbox, ContactRequest, Device, DeviceSet
from database.models.patient import Patient
from database.models.provider import Provider
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from security.access import get_current_active_patient, get_current_active_provider
from security.messaging import encrypt_contact
from sqlalchemy import select
from sqlalchemy.orm import Session, lazyload

router = APIRouter()

class PatientRequestInfo(BaseModel):
    provider_id: UUID
    message: str


@router.post("/message/request")
def patient_request(info: PatientRequestInfo, patient: Annotated[Patient, Depends(get_current_active_patient)]):
    session: Session
    with DBSession() as session:
        provider_key_mailbox_pairs = session.scalars(select(Device.identity_public_key, ContactMailbox).join(Device, Device.id == ContactMailbox.device_id).join(DeviceSet, DeviceSet.id == Device.device_set_id).where(DeviceSet.provider_id == info.provider_id).options(lazyload(ContactMailbox.messages))).all()
        if not provider_key_mailbox_pairs:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="PROVIDER MAILBOXES NOT FOUND")
        
        for key, mailbox in provider_key_mailbox_pairs:
            mailbox.messages.append(ContactRequest(patient_id_encrypted=encrypt_contact(str(patient.id), key), patient_message_encrypted=encrypt_contact(info.message, key)))

        session.commit()

class ContactMessage(BaseModel):
    created: datetime
    patient_id_encrypted: bytes
    patient_message_encrypted: bytes

@router.post("/message/contact/pending")
def provider_get_pending_contacts(device_id: UUID, provider: Annotated[Provider, Depends(get_current_active_provider)]) -> List[ContactMessage]:
    session: Session
    retrieved_messages: List[ContactMessage] = []
    with DBSession() as session:
        mailbox = session.scalar(select(ContactMailbox).where(ContactMailbox.device_id == device_id).options(lazyload(ContactMailbox.messages)))
        if mailbox:
            retrieved_messages = [ContactMessage(created=m.created, patient_id_encrypted=m.patient_id_encrypted, patient_message_encrypted=m.patient_message_encrypted) for m in mailbox.messages]
            mailbox.messages = []
            session.commit()
    return retrieved_messages