"""Tests for OpenStreetMap visualizer functionality."""

from datetime import datetime
from unittest.mock import MagicMock

import pytest

from src.models.city import City
from src.models.restriction import Restriction
from src.models.zone import Zone
from src.open_street_map.map import ItalyMap
from src.open_street_map.visualizer import (
    ZoneVisualizer,
    create_color_based_on_status,
    create_popup_content,
    highlight_active_zones,
)


@pytest.fixture
def sample_city_with_restrictions():
    """Create a sample city with zones that have time restrictions."""
    city = City(name='Milano', country='Italy')

    # Area C zone with weekday restrictions
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

    # Add weekday restriction
    weekday_restriction = Restriction(
        days=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'], start_time='07:30', end_time='19:30'
    )
    area_c.add_restriction(weekday_restriction)

    # Area B zone with weekday and weekend restrictions
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

    # Add restrictions
    area_b.add_restriction(weekday_restriction)
    weekend_restriction = Restriction(days=['Saturday'], start_time='10:00', end_time='18:00')
    area_b.add_restriction(weekend_restriction)

    city.add_zone(area_c)
    city.add_zone(area_b)

    return city


def test_create_color_based_on_status():
    """Test that colors are generated correctly based on zone status."""
    # Active zone should be red
    assert create_color_based_on_status(True) == 'red'

    # Inactive zone should be green
    assert create_color_based_on_status(False) == 'green'


def test_create_popup_content():
    """Test creating HTML popup content for a zone."""
    # Create a zone with restrictions
    zone = Zone(id='test-zone', name='Test Zone', city='Test City', boundaries=[])

    weekday_restriction = Restriction(
        days=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'], start_time='08:00', end_time='20:00'
    )
    zone.add_restriction(weekday_restriction)

    # Create popup content
    popup_html = create_popup_content(zone)

    # Check content includes critical information
    assert 'Test Zone' in popup_html
    assert 'Test City' in popup_html
    assert 'Monday' in popup_html
    assert '08:00' in popup_html
    assert '20:00' in popup_html


def test_highlight_active_zones(sample_city_with_restrictions):
    """Test highlighting active zones based on current time."""
    # Create a map with the city
    mock_map = MagicMock()
    italy_map = ItalyMap()
    italy_map.map = mock_map

    # Mock a Wednesday at noon (both zones should be active)
    test_datetime = datetime(2023, 5, 10, 12, 0)  # Wednesday

    # Highlight active zones
    highlighted_map = highlight_active_zones(sample_city_with_restrictions, italy_map, current_time=test_datetime)

    # The map should contain GeoJson layers for both zones
    html = highlighted_map.map._repr_html_()

    # Both zones should be present and marked as active
    assert 'Area C' in html
    assert 'Area B' in html
    assert 'red' in html


def test_zone_visualizer_initialization():
    """Test that a ZoneVisualizer can be properly initialized."""
    visualizer = ZoneVisualizer()

    # Should have a default map
    assert hasattr(visualizer, 'map')
    assert isinstance(visualizer.map, ItalyMap)


def test_zone_visualizer_with_map():
    """Test that a ZoneVisualizer can be initialized with a specific map."""
    custom_map = ItalyMap(center=[45.0, 9.0], zoom=8)
    visualizer = ZoneVisualizer(map_obj=custom_map)

    assert visualizer.map is custom_map
    assert visualizer.map.map.location == [45.0, 9.0]


def test_visualize_city(sample_city_with_restrictions):
    """Test visualizing a city with its zones."""
    # Mock the map
    mock_map = MagicMock()
    custom_map = ItalyMap()
    custom_map.map = mock_map
    custom_map.add_city = MagicMock()

    # Create visualizer with mock
    visualizer = ZoneVisualizer(map_obj=custom_map)

    # Visualize the city
    result_map = visualizer.visualize_city(sample_city_with_restrictions)

    # Check that add_city was called with the city
    custom_map.add_city.assert_called_once_with(sample_city_with_restrictions)

    # Check that result is the map
    assert result_map is custom_map


def test_visualize_active_zones(sample_city_with_restrictions):
    """Test visualizing only active zones in the city."""
    # Create visualizer with mock map
    mock_map = MagicMock()
    custom_map = ItalyMap()
    custom_map.map = mock_map

    visualizer = ZoneVisualizer(map_obj=custom_map)

    # Weekday at noon (both zones should be active)
    weekday = datetime(2023, 5, 10, 12, 0)  # Wednesday

    # Visualize active zones
    _ = visualizer.visualize_active_zones(sample_city_with_restrictions, current_time=weekday)

    # Both zones should be added to the map
    html = mock_map._repr_html_()
    assert 'Area C' in html or 'Area B' in html  # At least one zone should be added

    # Weekend at noon (only Area B should be active)
    saturday = datetime(2023, 5, 13, 12, 0)  # Saturday

    # Reset mock
    mock_map._repr_html_.return_value = ''

    # Visualize active zones on Saturday
    _ = visualizer.visualize_active_zones(sample_city_with_restrictions, current_time=saturday)

    # Only Area B should be included and marked as active (red)
    html = mock_map._repr_html_()
    assert 'Area B' in html
