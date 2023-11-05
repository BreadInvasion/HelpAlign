from uuid import UUID, uuid4

from database.models.base import UUIDC, Base
from database.models.messaging import DeviceSet
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column, relationship


class Patient(Base):
    """The base data structure representing an individual patient user."""

    __tablename__ = "patients"

    id: Mapped[UUID] = mapped_column(UUIDC, primary_key=True, default=uuid4)

    device_set: Mapped[DeviceSet] = relationship(back_populates="patient", uselist=False)

    given_name: Mapped[str] = mapped_column(String(50), nullable=False) # Internationalized for "first name"
    family_name: Mapped[str] = mapped_column(String(50), nullable=False) # Internationalized for "last name"

    is_assisted_account: Mapped[bool] = mapped_column(Boolean, nullable=False)
    guardian_given_name: Mapped[str] = mapped_column(String(50), nullable = True)
    guardian_family_name: Mapped[str] = mapped_column(String(50), nullable = True)
    
    email: Mapped[str] = mapped_column(String(254), nullable=False)

    password_hash: Mapped[str] = mapped_column(String, nullable=False)

