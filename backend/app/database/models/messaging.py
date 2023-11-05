from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, List, Optional
from uuid import UUID, uuid4

from database.models.base import UUIDC, Base
from sqlalchemy import DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, String, func
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from database.models.patient import Patient
    from database.models.provider import Provider


class UserType(Enum):
    PATIENT = 0
    PROVIDER = 1

class DeviceSet(Base):
    """The set of devices used by a patient or provider"""
    __tablename__ = "device_sets"

    id: Mapped[UUID] = mapped_column(UUIDC, primary_key=True, default=uuid4)

    user_type: Mapped[UserType] = mapped_column(SQLEnum(UserType), nullable=False)
    provider: Mapped[Optional["Provider"]] = relationship(back_populates="device_set", uselist=False)
    provider_id: Mapped[UUID | None] = mapped_column(ForeignKey("providers.id", ondelete='CASCADE'), nullable=True)
    patient: Mapped[Optional["Patient"]] = relationship(back_populates="device_set", uselist=False)
    patient_id: Mapped[UUID | None] = mapped_column(ForeignKey("patients.id", ondelete='CASCADE'), nullable=True)

    devices: Mapped[List["Device"]] = relationship(back_populates="device_set")

class Device(Base):
    """Representation of a single user device"""
    __tablename__ = "devices"

    id: Mapped[UUID] = mapped_column(UUIDC, primary_key=True, default=uuid4)

    mailbox: Mapped["Mailbox"] = relationship(back_populates="device", uselist=False)
    contact_mailbox: Mapped[Optional["ContactMailbox"]] = relationship(back_populates="device", uselist=False)

    identity_public_key: Mapped[str] = mapped_column(String, nullable=False)
    signed_pre_key: Mapped[str] = mapped_column(String, nullable=False)

    device_set: Mapped[DeviceSet] = relationship(back_populates="devices", uselist=False)
    device_set_id = mapped_column(ForeignKey("device_sets.id", ondelete='CASCADE'))

class Mailbox(Base):
    """Stores pending messages for a specific device"""
    __tablename__ = "mailboxes"

    id: Mapped[UUID] = mapped_column(UUIDC, primary_key=True, default=uuid4)

    device: Mapped[Device] = relationship(back_populates="mailbox", uselist=False)
    device_id: Mapped[UUID] = mapped_column(ForeignKey("devices.id", ondelete='CASCADE'))

    messages: Mapped[List["Message"]] = relationship(back_populates="mailbox")

class ContactMailbox(Base):
    """Stores pending contact requests for a specific provider device"""
    __tablename__ = "contact_mailboxes"

    id: Mapped[UUID] = mapped_column(UUIDC, primary_key=True, default=uuid4)

    device: Mapped[Device] = relationship(back_populates="contact_mailbox")
    device_id: Mapped[UUID] = mapped_column(ForeignKey("devices.id", ondelete='CASCADE'))

    messages: Mapped[List["ContactRequest"]] = relationship(back_populates="mailbox")

class Message(Base):
    """Stores an encrypted message between a provider and patient"""
    __tablename__ = "messages"

    message_id: Mapped[UUID] = mapped_column(UUIDC, primary_key=True, default=uuid4)
    message_encrypted: Mapped[bytes] = mapped_column(BYTEA, nullable=False)

    sender_id: Mapped[UUID] = mapped_column(UUIDC, nullable=False)
    sender_device_id: Mapped[UUID] = mapped_column(UUIDC, nullable=False)
    sender_identity_key: Mapped[str] = mapped_column(String, nullable=False)
    sender_ephemeral_key: Mapped[str | None] = mapped_column(String, nullable=True)
    chain_key: Mapped[str | None] = mapped_column(String, nullable=True)

    mailbox: Mapped[Mailbox] = relationship(back_populates="messages")
    mailbox_id: Mapped[UUID] = mapped_column(ForeignKey("mailboxes.id", ondelete='CASCADE'))

# TODO: automatically cull duplicate requests when the therapist pulls them to prevent spam
# TODO: patient blocklist for therapists? in order to maintain one-way encryption would have to cull when they retrieve the list
# TODO: auto-cull contact requests older than... two weeks?
class ContactRequest(Base):
    """Stores a contact request, fully encrypted with the public contact key of the target therapist."""

    __tablename__ = "contact_requests"

    id: Mapped[UUID] = mapped_column(UUIDC, primary_key=True, default=uuid4)
    created: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=func.now())

    mailbox: Mapped[ContactMailbox] = relationship(back_populates="messages") 
    mailbox_id: Mapped[UUID] = mapped_column(ForeignKey("contact_mailboxes.id", ondelete='CASCADE'))

    patient_id_encrypted: Mapped[bytes] = mapped_column(BYTEA, nullable=False)
    patient_message_encrypted: Mapped[bytes] = mapped_column(BYTEA, nullable=False)