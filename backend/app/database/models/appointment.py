from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from database.models.base import UUIDC, Base
from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import BYTEA
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

if TYPE_CHECKING:
    from database.models.provider import Provider


