"""Handles saving/loading zone data to/from disk."""

import json
from pathlib import Path

from src.models.city import City
from src.models.restriction import Restriction
from src.models.zone import Zone


def save_city(city: City, filepath: str | Path) -> None:
    """Save a city object to disk as a JSON file.

    Args:
        city: City object to save
        filepath: Path where to save the file
    """
    # Ensure directory exists
    filepath = Path(filepath)
    filepath.parent.mkdir(parents=True, exist_ok=True)

    # Convert city to serializable dict
    city_data = {'name': city.name, 'country': city.country, 'zones': []}

    # Add zones
    for zone in city.zones:
        zone_data = {
            'id': zone.id,
            'name': zone.name,
            'city': zone.city,
            'boundaries': zone.boundaries,
            'restrictions': [],
        }

        # Add restrictions
        for restriction in zone.restrictions:
            restriction_data = {
                'days': restriction.days,
                'start_time': f'{restriction.start_time.hour:02}:{restriction.start_time.minute:02}',
                'end_time': f'{restriction.end_time.hour:02}:{restriction.end_time.minute:02}',
                'vehicle_types': restriction.vehicle_types,
            }
            zone_data['restrictions'].append(restriction_data)

        city_data['zones'].append(zone_data)

    # Write to file
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(city_data, f, indent=2, ensure_ascii=False)


def load_city(filepath: str | Path) -> City:
    """Load a city object from a JSON file.

    Args:
        filepath: Path to the JSON file

    Returns:
        City: The loaded city object

    Raises:
        FileNotFoundError: If the file doesn't exist
        json.JSONDecodeError: If the file contains invalid JSON
    """
    filepath = Path(filepath)

    # Read file
    with open(filepath, encoding='utf-8') as f:
        city_data = json.load(f)

    # Create city object
    city = City(name=city_data['name'], country=city_data.get('country', 'Italy'))

    # Add zones
    for zone_data in city_data['zones']:
        zone = Zone(
            id=zone_data['id'], name=zone_data['name'], city=zone_data['city'], boundaries=zone_data['boundaries']
        )

        # Add restrictions
        for restriction_data in zone_data.get('restrictions', []):
            restriction = Restriction(
                days=restriction_data['days'],
                start_time=restriction_data['start_time'],
                end_time=restriction_data['end_time'],
                vehicle_types=restriction_data.get('vehicle_types', []),
            )
            zone.add_restriction(restriction)

        city.add_zone(zone)

    return city


def save_all_cities(cities: list[City], data_dir: str | Path) -> None:
    """Save a list of cities to disk, one file per city.

    Args:
        cities: List of City objects to save
        data_dir: Directory where to save the files
    """
    data_dir = Path(data_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    for city in cities:
        # Use lowercase city name for filename
        filename = f'{city.name.lower()}.json'
        filepath = data_dir / filename
        save_city(city, filepath)


def load_all_cities(data_dir: str | Path) -> list[City]:
    """Load all cities from JSON files in a directory.

    Args:
        data_dir: Directory containing city JSON files

    Returns:
        List of City objects
    """
    data_dir = Path(data_dir)
    cities = []

    # Find all JSON files
    json_files = list(data_dir.glob('*.json'))

    for file_path in json_files:
        try:
            city = load_city(file_path)
            cities.append(city)
        except (json.JSONDecodeError, KeyError) as e:
            # Log error but continue with other files
            print(f'Error loading {file_path}: {e}')

    return cities
