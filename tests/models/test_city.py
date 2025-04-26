"""Tests for the City model."""

from src.models.city import City
from src.models.zone import Zone


def test_city_initialization():
    """Test that a city can be properly initialized."""
    city_name = 'Milano'
    country = 'Italy'

    city = City(name=city_name, country=country)

    assert city.name == city_name
    assert city.country == country
    assert city.zones == []


def test_add_zone():
    """Test that zones can be added to a city."""
    city = City(name='Roma')

    zone1 = Zone(id='roma-ztl-1', name='ZTL Centro', city='Roma', boundaries=[])
    zone2 = Zone(id='roma-ztl-2', name='ZTL Trastevere', city='Roma', boundaries=[])

    city.add_zone(zone1)
    city.add_zone(zone2)

    assert len(city.zones) == 2
    assert city.zones[0] == zone1
    assert city.zones[1] == zone2


def test_get_zone_by_id():
    """Test that zones can be retrieved by ID."""
    city = City(name='Firenze')

    zone1 = Zone(id='firenze-ztl-a', name='ZTL A', city='Firenze', boundaries=[])
    zone2 = Zone(id='firenze-ztl-b', name='ZTL B', city='Firenze', boundaries=[])

    city.add_zone(zone1)
    city.add_zone(zone2)

    retrieved_zone = city.get_zone_by_id('firenze-ztl-b')

    assert retrieved_zone is not None
    assert retrieved_zone.id == 'firenze-ztl-b'
    assert retrieved_zone.name == 'ZTL B'

    # Test non-existent zone
    assert city.get_zone_by_id('non-existent') is None


def test_to_geojson():
    """Test that a city can be converted to GeoJSON format."""
    city = City(name='Bologna')

    # Add a couple of zones
    zone1 = Zone(
        id='bologna-ztl-1',
        name='ZTL Centro Storico',
        city='Bologna',
        boundaries=[[11.34, 44.49], [11.35, 44.49], [11.35, 44.48], [11.34, 44.48], [11.34, 44.49]],
    )

    zone2 = Zone(
        id='bologna-ztl-2',
        name='ZTL Università',
        city='Bologna',
        boundaries=[[11.35, 44.50], [11.36, 44.50], [11.36, 44.49], [11.35, 44.49], [11.35, 44.50]],
    )

    city.add_zone(zone1)
    city.add_zone(zone2)

    geojson = city.to_geojson()

    assert geojson['type'] == 'FeatureCollection'
    assert len(geojson['features']) == 2
    assert geojson['properties']['name'] == 'Bologna'
    assert geojson['properties']['country'] == 'Italy'
    assert geojson['properties']['zone_count'] == 2

    # Check first feature
    assert geojson['features'][0]['properties']['id'] == 'bologna-ztl-1'
    assert geojson['features'][0]['properties']['name'] == 'ZTL Centro Storico'

    # Check second feature
    assert geojson['features'][1]['properties']['id'] == 'bologna-ztl-2'
    assert geojson['features'][1]['properties']['name'] == 'ZTL Università'
