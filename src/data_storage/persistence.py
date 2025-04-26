"""Handles saving/loading zone data to/from disk."""

import json
import os
from pathlib import Path

from src.models.city import City
from src.models.restriction import Restriction
from src.models.zone import Zone

# Default directory for storing city data
DEFAULT_DATA_DIR = Path(__file__).parent.parent.parent / 'data' / 'cities'


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


def load_city(name: str | Path, data_dir: str | Path = DEFAULT_DATA_DIR) -> City | None:
    """Load a city object from a JSON file.

    Args:
        name: Name of the city or path to the JSON file
        data_dir: Directory containing city data files (if name is a city name)

    Returns:
        City: The loaded city object, or None if not found

    Raises:
        json.JSONDecodeError: If the file contains invalid JSON
    """
    # Determine the file path
    if isinstance(name, Path) or (isinstance(name, str) and os.path.isfile(name)):
        filepath = Path(name)
    else:
        # Convert city name to lowercase for filename
        filename = f'{name.lower()}.json'
        filepath = Path(data_dir) / filename

    # Check if file exists
    if not filepath.exists():
        return None

    # Read file
    try:
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
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        return None


def save_all_cities(cities: list[City], data_dir: str | Path = DEFAULT_DATA_DIR) -> None:
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


def load_all_cities(data_dir: str | Path = DEFAULT_DATA_DIR) -> list[City]:
    """Load all cities from JSON files in a directory.

    Args:
        data_dir: Directory containing city JSON files

    Returns:
        List of City objects
    """
    data_dir = Path(data_dir)
    cities: list[City] = []

    # Ensure directory exists
    if not data_dir.exists():
        return cities

    # Find all JSON files
    json_files = list(data_dir.glob('*.json'))

    for file_path in json_files:
        try:
            city = load_city(file_path)
            if city:
                cities.append(city)
        except (json.JSONDecodeError, KeyError) as e:
            # Log error but continue with other files
            print(f'Error loading {file_path}: {e}')

    return cities


def get_all_cities(data_dir: str | Path = DEFAULT_DATA_DIR) -> list[dict[str, str]]:
    """Get a list of all available cities with their country.

    Args:
        data_dir: Directory containing city data files

    Returns:
        List of dictionaries with city name and country
    """
    cities = load_all_cities(data_dir)
    return [{'name': city.name, 'country': city.country} for city in cities]
