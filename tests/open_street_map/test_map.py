"""Tests for OpenStreetMap mapping functionality."""

from unittest.mock import MagicMock

import folium
import pytest

from src.models.city import City
from src.models.zone import Zone
from src.open_street_map.map import ItalyMap, create_map_for_city, save_map


@pytest.fixture
def sample_city():
    """Create a sample city with zones for testing."""
    city = City(name='Milano', country='Italy')

    # Create Area C zone
    area_c = Zone(
        id='milano-area-c',
        name='Area C',
        city='Milano',
        boundaries=[
            [9.1859, 45.4654],
            [9.1897, 45.4675],
            [9.1923, 45.4662],
            [9.1883, 45.4641],
            [9.1859, 45.4654],
        ],
    )

    # Create Area B zone
    area_b = Zone(
        id='milano-area-b',
        name='Area B',
        city='Milano',
        boundaries=[
            [9.1700, 45.4600],
            [9.1800, 45.4700],
            [9.1900, 45.4650],
            [9.1750, 45.4550],
            [9.1700, 45.4600],
        ],
    )

    city.add_zone(area_c)
    city.add_zone(area_b)

    return city


def test_italy_map_initialization():
    """Test that an Italy map can be created with expected defaults."""
    italy_map = ItalyMap()

    # Check that the map is a folium Map
    assert isinstance(italy_map.map, folium.Map)

    # Check default center coordinates (roughly center of Italy)
    assert italy_map.map.location == [42.5, 12.5]

    # Check default zoom level
    assert italy_map.map.zoom_start == 6


def test_italy_map_custom_parameters():
    """Test that ItalyMap can be created with custom parameters."""
    custom_map = ItalyMap(
        center=[45.4642, 9.1900],  # Milan
        zoom=10,
        tiles='CartoDB positron',
    )

    assert custom_map.map.location == [45.4642, 9.1900]
    assert custom_map.map.zoom_start == 10
    assert 'CartoDB positron' in str(custom_map.map)


def test_create_map_for_city(sample_city):
    """Test creating a map for a specific city."""
    city_map = create_map_for_city(sample_city)

    # Check map is properly centered on city (Milan)
    assert abs(city_map.map.location[0] - 45.46) < 0.1  # Approx latitude
    assert abs(city_map.map.location[1] - 9.19) < 0.1  # Approx longitude

    # Check that the map contains polygons for the zones
    # This checks the HTML content for GeoJson features
    html = city_map.map._repr_html_()
    assert 'GeoJson' in html
    assert 'Area C' in html
    assert 'Area B' in html


def test_save_map(tmp_path):
    """Test saving a map to an HTML file."""
    mock_map = MagicMock()
    mock_map._repr_html_.return_value = '<html>Mock Map Content</html>'

    # Use a fake save method
    mock_map.save = MagicMock()

    italy_map = ItalyMap()
    italy_map.map = mock_map

    # Save to temporary file
    output_file = tmp_path / 'test_map.html'
    save_map(italy_map, output_file)

    # Check that save was called
    mock_map.save.assert_called_once_with(str(output_file))


def test_add_zone_to_map(sample_city):
    """Test adding a zone to a map."""
    italy_map = ItalyMap()

    # Get a zone from the sample city
    zone = sample_city.zones[0]

    # Add the zone to the map
    italy_map.add_zone(zone)

    # Check that the map contains the zone
    html = italy_map.map._repr_html_()
    assert zone.name in html

    # Check properties are included
    assert zone.id in html


def test_add_city_to_map(sample_city):
    """Test adding an entire city to a map."""
    italy_map = ItalyMap()

    # Add the city to the map
    italy_map.add_city(sample_city)

    # Check that the map contains all zones
    html = italy_map.map._repr_html_()
    for zone in sample_city.zones:
        assert zone.name in html

    # Check city name is included as a layer name
    assert sample_city.name in html
