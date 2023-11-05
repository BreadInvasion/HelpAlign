from typing import Tuple

from config.config import settings
from googlemaps import Client
from pydantic import BaseModel


class Geocode(BaseModel):
    latitude: float
    longitude: float

    def as_tuple(self) -> Tuple[float, float]:
        return (self.latitude, self.longitude)

class ValidationData(BaseModel):
    formatted_address: str
    state_abbreviation: str
    geocode: Geocode

class AddressNotValidException(Exception):
    """Returned when the google API does not confirm that the provided address is valid"""
    pass

gmaps: Client = Client(key=settings.gmaps_key)

def validate_address(street_address, city, state_abbreviation, zip_code, unit) -> ValidationData:
    response = gmaps.addressvalidation(([street_address, unit] if unit else [street_address]) + [f"{city}, {state_abbreviation}, {zip_code}"], regionCode='US', enableUspsCass=True) # type: ignore
    try:
        if response["result"]["verdict"]["addressComplete"] and response["result"]["verdict"]["validationGranularity"] in ["PREMISE", "SUB_PREMISE"]:
            return ValidationData(
                                formatted_address=response["result"]["address"]["formattedAddress"], 
                                state_abbreviation=response["result"]["uspsData"]["standardizedAddress"]["state"],
                                geocode=Geocode(
                                    latitude=response["result"]["geocode"]["location"]["latitude"],
                                    longitude=response["result"]["geocode"]["location"]["longitude"]
                                    )
                                )
    except KeyError:
        pass #flows to raise
    raise AddressNotValidException


def geocode_address(street_address, city, state_abbreviation) -> Tuple[float, float] | None:
    results = gmaps.geocode(f"{street_address}, f{city}, f{state_abbreviation}") # type: ignore
    if not len(results):
        return None
    try:
        return (results[0]["geometry"]["location"]["lat"], results[0]["geometry"]["location"]["long"])
    except KeyError:
        return None