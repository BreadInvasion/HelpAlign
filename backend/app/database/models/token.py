from uuid import UUID, uuid4

from database.models.base import UUIDC, Base
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class PatientDBToken(Base):
    __tablename__ = "patient_access_tokens"

    instance_id: Mapped[UUID] = mapped_column(UUIDC, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUIDC, nullable=False)
    token_hash: Mapped[str] = mapped_column(String, primary_key=True)

class ProviderDBToken(Base):
    __tablename__ = "provider_access_tokens"

    instance_id: Mapped[UUID] = mapped_column(UUIDC, primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(UUIDC, nullable=False)
    token_hash: Mapped[str] = mapped_column(String, primary_key=True)