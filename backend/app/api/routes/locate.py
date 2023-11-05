from enum import Enum
from typing import List
from uuid import UUID

from api.maps import Geocode, geocode_address
from database.database import DBSession
from database.models.provider import (
    AcceptingNewPatients,
    Provider,
    ProviderGenderIdentity,
    ProviderType,
)
from fastapi import APIRouter
from haversine import Unit, haversine
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter()

US_STATES = [ 'AK', 'AL', 'AR', 'AZ', 'CA', 'CO', 'CT', 'DC', 'DE', 'FL', 'GA',
           'HI', 'IA', 'ID', 'IL', 'IN', 'KS', 'KY', 'LA', 'MA', 'MD', 'ME',
           'MI', 'MN', 'MO', 'MS', 'MT', 'NC', 'ND', 'NE', 'NH', 'NJ', 'NM',
           'NV', 'NY', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC', 'SD', 'TN', 'TX',
           'UT', 'VA', 'VT', 'WA', 'WI', 'WV', 'WY']

USStatesEnum = Enum('USStatesEnum', US_STATES)

class LocateFilters(BaseModel):
    provider_gender_identity_allow: List[ProviderGenderIdentity]
    accepting_new_patients_allow: List[AcceptingNewPatients]
    provider_type: ProviderType
    include_remote: bool
    remote_only: bool

class LocateInfo(BaseModel):
    filters: LocateFilters
    street_address: str
    city: str
    state_abbreviation: USStatesEnum
    radius: int

class Name(BaseModel):
    given: str
    family: str

class FormattedLocation(BaseModel):
    formatted_address: str
    geocode: Geocode

class LocateRelevantProviderInfo(BaseModel):
    provider_id: UUID
    provider_name: Name
    provider_gender_identity: str
    provider_location: FormattedLocation

class InvalidRowOutputException(Exception):
    """Raised when a scalar output of a custom row doesn't return the expected number or type of values"""
    pass

def locater_row_to_object(row) -> LocateRelevantProviderInfo:
    if len(row) != 7:
        raise InvalidRowOutputException
    try:
        return LocateRelevantProviderInfo(provider_id=row[0], 
                                          provider_name=Name(
                                                             given=row[1], 
                                                             family=row[2]
                                                            ), 
                                          provider_gender_identity=row[3], 
                                          provider_location=FormattedLocation(
                                                                              formatted_address=row[4], 
                                                                              geocode=Geocode(
                                                                                              latitude=row[5], 
                                                                                              longitude=row[6]
                                                                                            )
                                                                            )
                                        )
    except ValueError:
        raise InvalidRowOutputException

@router.post("/locate/nearby")
def locate_nearby_providers(info: LocateInfo) -> List[LocateRelevantProviderInfo]:
    """Returns a list of provider info for providers within radius miles of the user's location, who fit the provided filters"""
    info.radius = min(info.radius, 100) # cap out at 100 miles
    if info.filters.remote_only:
        info.filters.include_remote = True
    valid_remote_status = set([info.filters.remote_only, info.filters.include_remote]) # true for both if remote_only, so only true. true false if remote_only is false but include_remote is true. false if both are false.

    results = None
    session: Session
    with DBSession() as session:
        results = session.scalars(select(Provider.id, Provider.given_name, Provider.family_name, Provider.gender_identity, Provider.formatted_address, Provider.latitude, Provider.longitude).where(
                                                        Provider.state_abbreviation == info.state_abbreviation.name,
                                                        Provider.accepting_new_patients.in_(info.filters.accepting_new_patients_allow),
                                                        Provider.gender_identity.in_(info.filters.provider_gender_identity_allow),
                                                        Provider.provider_type == info.filters.provider_type,
                                                        Provider.remote_available.in_(valid_remote_status),
                                                        )
                                                    ).all()
        
        geoloc = geocode_address(street_address=info.street_address, city=info.city, state_abbreviation=info.state_abbreviation.name)
        results_formatted = [locater_row_to_object(row) for row in results]
        results_distance_restricted = [obj for obj in results_formatted if haversine(geoloc, obj.provider_location.geocode.as_tuple(), unit=Unit.MILES) < info.radius]
        return results_distance_restricted