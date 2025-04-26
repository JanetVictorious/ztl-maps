"""Tests for data persistence functionality."""

import json

import pytest

from src.data_storage.persistence import (
    get_all_cities,
    load_all_cities,
    load_city,
    save_all_cities,
    save_city,
)
from src.models.city import City
from src.models.restriction import Restriction
from src.models.zone import Zone


@pytest.fixture
def sample_city():
    """Create a sample city with zones for testing."""
    city = City(name='Milano', country='Italy')

    # Area C zone
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

    # Area B zone
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

    # Add zones to city
    city.add_zone(area_c)
    city.add_zone(area_b)

    return city


def test_save_city(sample_city, tmp_path):
    """Test saving a city to disk as JSON."""
    # Save city to temporary file
    filepath = tmp_path / 'milano.json'
    save_city(sample_city, filepath)

    # Check that file exists
    assert filepath.exists()

    # Read the content and verify it's valid JSON
    with open(filepath) as f:
        data = json.load(f)

    # Check JSON content
    assert data['name'] == 'Milano'
    assert data['country'] == 'Italy'
    assert len(data['zones']) == 2
    assert data['zones'][0]['id'] == 'milano-area-c'
    assert data['zones'][1]['id'] == 'milano-area-b'


def test_load_city(sample_city, tmp_path):
    """Test loading a city from disk."""
    # Save city to temporary file
    filepath = tmp_path / 'milano.json'
    save_city(sample_city, filepath)

    # Load city from file
    loaded_city = load_city(filepath)

    # Verify loaded city matches original
    assert loaded_city.name == sample_city.name
    assert loaded_city.country == sample_city.country
    assert len(loaded_city.zones) == len(sample_city.zones)

    # Check specific zone details
    assert loaded_city.zones[0].id == sample_city.zones[0].id
    assert loaded_city.zones[0].name == sample_city.zones[0].name
    assert len(loaded_city.zones[0].restrictions) == len(sample_city.zones[0].restrictions)

    # Verify we can use the restored object methods
    assert loaded_city.get_zone_by_id('milano-area-c') is not None


def test_save_and_load_all_cities(sample_city, tmp_path):
    """Test saving and loading multiple cities."""
    # Create a second city
    roma = City(name='Roma', country='Italy')
    ztl_centro = Zone(
        id='roma-ztl-centro',
        name='ZTL Centro Storico',
        city='Roma',
        boundaries=[
            [12.4814, 41.8933],
            [12.4914, 41.9033],
            [12.5014, 41.8933],
            [12.4914, 41.8833],
            [12.4814, 41.8933],
        ],
    )
    roma.add_zone(ztl_centro)

    cities = [sample_city, roma]

    # Save all cities
    data_dir = tmp_path / 'cities'
    save_all_cities(cities, data_dir)

    # Verify files were created
    assert (data_dir / 'milano.json').exists()
    assert (data_dir / 'roma.json').exists()

    # Load all cities
    loaded_cities = load_all_cities(data_dir)

    # Verify correct number of cities loaded
    assert len(loaded_cities) == 2

    # Check city names were loaded correctly
    city_names = [city.name for city in loaded_cities]
    assert 'Milano' in city_names
    assert 'Roma' in city_names

    # Check specific city details
    milano = next(city for city in loaded_cities if city.name == 'Milano')
    assert len(milano.zones) == 2
    assert milano.get_zone_by_id('milano-area-b') is not None


def test_load_nonexistent_file(tmp_path):
    """Test loading a file that doesn't exist."""
    nonexistent_file = tmp_path / 'nonexistent.json'

    # Now returns None instead of raising FileNotFoundError
    result = load_city(nonexistent_file)
    assert result is None


def test_load_invalid_json(tmp_path):
    """Test loading an invalid JSON file."""
    # Create invalid JSON file
    invalid_file = tmp_path / 'invalid.json'
    with open(invalid_file, 'w') as f:
        f.write('{invalid json')

    # Now returns None instead of raising JSONDecodeError
    result = load_city(invalid_file)
    assert result is None


def test_load_city_by_name(sample_city, tmp_path):
    """Test loading a city by name."""
    # Set up a temporary data directory
    data_dir = tmp_path / 'cities'
    data_dir.mkdir(parents=True, exist_ok=True)

    # Save a city
    filepath = data_dir / 'milano.json'
    save_city(sample_city, filepath)

    # Load the city by name
    loaded_city = load_city('Milano', data_dir)

    # Verify loaded city matches original
    assert loaded_city is not None
    assert loaded_city.name == 'Milano'
    assert loaded_city.country == 'Italy'

    # Try loading a nonexistent city
    nonexistent_city = load_city('NonExistentCity', data_dir)
    assert nonexistent_city is None


def test_get_all_cities(tmp_path):
    """Test getting a list of all available cities."""
    # Create and save sample cities
    data_dir = tmp_path / 'cities'
    data_dir.mkdir(parents=True, exist_ok=True)

    # Create cities
    milano = City(name='Milano', country='Italy')
    roma = City(name='Roma', country='Italy')
    paris = City(name='Paris', country='France')

    # Save cities
    save_city(milano, data_dir / 'milano.json')
    save_city(roma, data_dir / 'roma.json')
    save_city(paris, data_dir / 'paris.json')

    # Get list of all cities
    cities_list = get_all_cities(data_dir)

    # Verify result
    assert len(cities_list) == 3
    assert {'name': 'Milano', 'country': 'Italy'} in cities_list
    assert {'name': 'Roma', 'country': 'Italy'} in cities_list
    assert {'name': 'Paris', 'country': 'France'} in cities_list

    # Test with empty directory
    empty_dir = tmp_path / 'empty'
    empty_dir.mkdir(parents=True, exist_ok=True)
    assert get_all_cities(empty_dir) == []

    # Test with nonexistent directory
    nonexistent_dir = tmp_path / 'nonexistent'
    assert get_all_cities(nonexistent_dir) == []
