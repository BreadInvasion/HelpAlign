from enum import Enum
from typing import List
from uuid import UUID, uuid4

from database.models.base import UUIDC, Base
from database.models.messaging import DeviceSet
from sqlalchemy import Boolean
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Float, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class ProviderGenderIdentity(Enum):
    MALE = 0
    FEMALE = 1
    OTHER = 2

class ProviderType(Enum):
    THERAPIST = 0
    PSYCHIATRIST = 1

class AcceptingNewPatients(Enum):
    RED = 0
    YELLOW = 1
    GREEN = 2

class Provider(Base):
    """The base data structure representing an individual Provider user."""

    __tablename__ = "providers"

    #BACKEND REFERENCE
    id: Mapped[UUID] = mapped_column(UUIDC, primary_key=True, default=uuid4)

    device_set: Mapped[DeviceSet] = relationship(back_populates="provider", uselist=False)

    #SEARCH FILTERS
    provider_type: Mapped[ProviderType] = mapped_column(SQLEnum(ProviderType), nullable=False)
    remote_available: Mapped[bool] = mapped_column(Boolean, nullable=False)
    accepting_new_patients: Mapped[AcceptingNewPatients] = mapped_column(SQLEnum(AcceptingNewPatients), nullable=False)
    gender_identity: Mapped[ProviderGenderIdentity] = mapped_column(SQLEnum(ProviderGenderIdentity), nullable=False)

    #PERSONAL INFORMATION
    given_name: Mapped[str] = mapped_column(String(50), nullable=False) # Internationalized for "first name"
    family_name: Mapped[str] = mapped_column(String(50), nullable=False) # Internationalized for "last name"

    #LOCATION
    formatted_address: Mapped[str] = mapped_column(String, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    state_abbreviation: Mapped[str] = mapped_column(String, nullable=False)

    #LOGIN DETAILS
    email: Mapped[str] = mapped_column(String(254), nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)