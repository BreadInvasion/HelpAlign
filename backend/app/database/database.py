from config.config import settings
from database.models.base import Base
from database.models.messaging import (
    ContactMailbox,
    ContactRequest,
    Device,
    DeviceSet,
    Mailbox,
    Message,
)
from database.models.patient import Patient
from database.models.provider import Provider
from database.models.token import PatientDBToken, ProviderDBToken
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(settings.db_url)
Base.metadata.create_all(engine)
# Device.metadata.create_all(engine)
# DeviceSet.metadata.create_all(engine)
# Mailbox.metadata.create_all(engine)
# ContactMailbox.metadata.create_all(engine)
# Message.metadata.create_all(engine)
# ContactRequest.metadata.create_all(engine)
# Patient.metadata.create_all(engine)
# Provider.metadata.create_all(engine)
# PatientDBToken.metadata.create_all(engine)
# ProviderDBToken.metadata.create_all(engine)

DBSession: sessionmaker = sessionmaker(engine)