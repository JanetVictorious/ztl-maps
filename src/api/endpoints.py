"""API endpoints for accessing zone data programmatically."""

from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from src.data_storage.persistence import get_all_cities, load_city


class Zone(BaseModel):
    """Pydantic model for zone data."""

    id: str
    name: str
    city: str
    is_active: bool = False


class City(BaseModel):
    """Pydantic model for city data."""

    name: str
    country: str
    zones: list[Zone] = []


app = FastAPI(title='ZTL Maps API', description='API for accessing ZTL zone data')


@app.get('/cities', response_model=list[dict])
def get_cities():
    """Get a list of all available cities."""
    return get_all_cities()


@app.get('/cities/{city_name}', response_model=City)
def get_city(city_name: str):
    """Get information about a specific city."""
    city = load_city(city_name)
    if not city:
        raise HTTPException(status_code=404, detail=f"City '{city_name}' not found")

    # Convert to Pydantic model for serialization
    return City(
        name=city.name,
        country=city.country,
        zones=[
            Zone(id=zone.id, name=zone.name, city=zone.city, is_active=zone.is_active_at(datetime.now()))
            for zone in city.zones
        ],
    )


@app.get('/cities/{city_name}/active-zones', response_model=list[Zone])
def get_active_zones(city_name: str):
    """Get all active zones for a specific city at the current time."""
    city = load_city(city_name)
    if not city:
        raise HTTPException(status_code=404, detail=f"City '{city_name}' not found")

    current_time = datetime.now()
    active_zones = []

    for zone in city.zones:
        if zone.is_active_at(current_time):
            active_zones.append(Zone(id=zone.id, name=zone.name, city=zone.city, is_active=True))

    return active_zones
