from datetime import datetime

from src.models.restriction import Restriction
from src.models.zone import Zone


def test_zone_initialization():
    """Test that a zone can be properly initialized with all expected attributes."""
    zone_id = 'milano-c'
    name = 'Area C'
    city = 'Milano'
    boundaries = [
        [9.1859, 45.4654],
        [9.1897, 45.4675],
        [9.1923, 45.4662],
        [9.1883, 45.4641],
        [9.1859, 45.4654],
    ]

    zone = Zone(id=zone_id, name=name, city=city, boundaries=boundaries)

    assert zone.id == zone_id
    assert zone.name == name
    assert zone.city == city
    assert zone.boundaries == boundaries
    assert zone.restrictions == []


def test_add_restriction():
    """Test that restrictions can be added to a zone."""
    zone = Zone(id='roma-ztl', name='ZTL Centro', city='Roma', boundaries=[])

    # Create a restriction (will need to implement Restriction class later)
    restriction = Restriction(
        days=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'], start_time='07:30', end_time='19:30'
    )

    zone.add_restriction(restriction)

    assert len(zone.restrictions) == 1
    assert zone.restrictions[0] == restriction


def test_is_active_at():
    """Test that the zone correctly determines if it's active at a given time."""
    zone = Zone(id='firenze-ztl', name='ZTL Firenze', city='Firenze', boundaries=[])

    # Add weekday restriction
    weekday_restriction = Restriction(
        days=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'], start_time='07:30', end_time='19:30'
    )

    # Add weekend restriction
    weekend_restriction = Restriction(days=['Saturday'], start_time='10:00', end_time='16:00')

    zone.add_restriction(weekday_restriction)
    zone.add_restriction(weekend_restriction)

    # Test weekday during active hours
    wednesday_active = datetime(2023, 5, 10, 12, 0)  # Wednesday at noon
    assert zone.is_active_at(wednesday_active) is True

    # Test weekday outside active hours
    wednesday_inactive = datetime(2023, 5, 10, 20, 0)  # Wednesday at 8 PM
    assert zone.is_active_at(wednesday_inactive) is False

    # Test weekend during active hours
    saturday_active = datetime(2023, 5, 13, 12, 0)  # Saturday at noon
    assert zone.is_active_at(saturday_active) is True

    # Test weekend outside active hours
    saturday_inactive = datetime(2023, 5, 13, 17, 0)  # Saturday at 5 PM
    assert zone.is_active_at(saturday_inactive) is False

    # Test Sunday (no restrictions)
    sunday = datetime(2023, 5, 14, 12, 0)  # Sunday at noon
    assert zone.is_active_at(sunday) is False


def test_to_geojson():
    """Test that a zone can be converted to GeoJSON format."""
    zone = Zone(
        id='bologna-ztl',
        name='ZTL Centro Storico',
        city='Bologna',
        boundaries=[
            [11.3402, 44.4937],
            [11.3458, 44.4948],
            [11.3467, 44.4925],
            [11.3411, 44.4913],
            [11.3402, 44.4937],
        ],
    )

    geojson = zone.to_geojson()

    assert geojson['type'] == 'Feature'
    assert geojson['properties']['id'] == 'bologna-ztl'
    assert geojson['properties']['name'] == 'ZTL Centro Storico'
    assert geojson['properties']['city'] == 'Bologna'
    assert geojson['geometry']['type'] == 'Polygon'
    assert len(geojson['geometry']['coordinates'][0]) == 5
