"""Helper functions for web scraping operations."""

import json
import re
from typing import Any


def parse_coordinates(  # pylint: disable=too-many-branches
    coords_data: Any,
    format_type: str = 'semicolon',
) -> list[list[float]]:
    """Parse coordinates from different string formats into a list of [longitude, latitude] pairs.

    Args:
        coords_data: Coordinate data in various formats (string, list, etc.)
        format_type: Format type of the coordinates. Options:
            - 'semicolon': "lon1,lat1;lon2,lat2;..."
            - 'geojson': GeoJSON formatted string or dict
            - 'brackets': "[[lon1,lat1], [lon2,lat2], ...]"
            - 'space': "lon1 lat1 lon2 lat2 ..."

    Returns:
        List of [longitude, latitude] pairs
    """
    coordinates = []

    if isinstance(coords_data, str):
        if format_type == 'semicolon':
            # Format: "lon1,lat1;lon2,lat2;..."
            pairs = coords_data.split(';')
            for pair in pairs:
                if ',' in pair:
                    lon, lat = pair.split(',')
                    coordinates.append([float(lon.strip()), float(lat.strip())])

        elif format_type == 'geojson':
            # Parse GeoJSON string
            try:
                geojson_data = json.loads(coords_data)
                coordinates = extract_coordinates_from_geojson(geojson_data)
            except json.JSONDecodeError as err:
                raise ValueError(f'Invalid GeoJSON string: {coords_data}') from err

        elif format_type == 'brackets':
            # Format: "[[lon1,lat1], [lon2,lat2], ...]"
            try:
                coords_list = json.loads(coords_data)
                for pair in coords_list:
                    if len(pair) >= 2:
                        coordinates.append([float(pair[0]), float(pair[1])])
            except json.JSONDecodeError:
                # Try regex pattern
                pattern = r'\[([^[\]]+),\s*([^[\]]+)\]'
                matches = re.findall(pattern, coords_data)
                for lon, lat in matches:
                    coordinates.append([float(lon.strip()), float(lat.strip())])

        elif format_type == 'space':
            # Format: "lon1 lat1 lon2 lat2 ..."
            values = coords_data.split()
            if len(values) % 2 == 0:
                for i in range(0, len(values), 2):
                    coordinates.append([float(values[i]), float(values[i + 1])])

    elif isinstance(coords_data, dict) and format_type == 'geojson':
        # Parse GeoJSON dict
        coordinates = extract_coordinates_from_geojson(coords_data)

    elif isinstance(coords_data, list):
        # Already a list, validate format
        for pair in coords_data:
            if isinstance(pair, list) and len(pair) >= 2:
                coordinates.append([float(pair[0]), float(pair[1])])

    return coordinates


def extract_coordinates_from_geojson(geojson_data: dict[str, Any]) -> list[list[float]]:
    """Extract coordinates from a GeoJSON object.

    Args:
        geojson_data: GeoJSON data as a dict

    Returns:
        List of [longitude, latitude] pairs
    """
    coordinates = []

    if 'type' in geojson_data:
        geom_type = geojson_data.get('type', '')

        if geom_type == 'Feature' and 'geometry' in geojson_data:
            # Extract from Feature
            return extract_coordinates_from_geojson(geojson_data['geometry'])

        if geom_type == 'FeatureCollection' and 'features' in geojson_data:
            # Extract from all features
            features = geojson_data['features']
            for feature in features:
                coords = extract_coordinates_from_geojson(feature)
                coordinates.extend(coords)

        elif geom_type == 'Point' and 'coordinates' in geojson_data:
            # Point geometry
            point = geojson_data['coordinates']
            coordinates.append([float(point[0]), float(point[1])])

        elif geom_type == 'LineString' and 'coordinates' in geojson_data:
            # LineString geometry
            coordinates = [[float(point[0]), float(point[1])] for point in geojson_data['coordinates']]

        elif (
            geom_type == 'Polygon'
            and 'coordinates' in geojson_data
            and geojson_data['coordinates']
            and geojson_data['coordinates'][0]
        ):
            # Polygon geometry - use the outer ring (first ring)
            coordinates = [[float(point[0]), float(point[1])] for point in geojson_data['coordinates'][0]]

    return coordinates


def extract_time_ranges(text: str) -> list[tuple[list[str] | None, str, str]]:  # pylint: disable=too-many-locals
    """Extract time ranges from text descriptions.

    Args:
        text: Text describing operating times, e.g. "Monday-Friday 7:30-19:30, Saturday 10:00-18:00"

    Returns:
        List of tuples (days, start_time, end_time)
        days: List of day names or None if days not found
        start_time: Start time as string in format "HH:MM"
        end_time: End time as string in format "HH:MM"
    """
    results: list[tuple[list[str] | None, str, str]] = []

    # Split by comma for multiple time ranges
    time_ranges = text.split(',')

    for time_range in time_ranges:
        time_range = time_range.strip()

        # Pattern: "Monday-Friday 7:30-19:30"
        day_range_match = re.search(r'([A-Za-z]+)-([A-Za-z]+)\s+(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})', time_range)
        if day_range_match:
            start_day = day_range_match.group(1)
            end_day = day_range_match.group(2)

            # Expand day range
            days = expand_day_range(start_day, end_day)

            start_hour = day_range_match.group(3).zfill(2)
            start_min = day_range_match.group(4)
            end_hour = day_range_match.group(5).zfill(2)
            end_min = day_range_match.group(6)

            start_time = f'{start_hour}:{start_min}'
            end_time = f'{end_hour}:{end_min}'

            results.append((days, start_time, end_time))
            continue

        # Pattern: "Saturday 10:00-18:00"
        single_day_match = re.search(r'([A-Za-z]+)\s+(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})', time_range)
        if single_day_match:
            day = single_day_match.group(1)
            days = [day]

            start_hour = single_day_match.group(2).zfill(2)
            start_min = single_day_match.group(3)
            end_hour = single_day_match.group(4).zfill(2)
            end_min = single_day_match.group(5)

            start_time = f'{start_hour}:{start_min}'
            end_time = f'{end_hour}:{end_min}'

            results.append((days, start_time, end_time))
            continue

        # Pattern: "7:30-19:30" (no days specified)
        time_only_match = re.search(r'(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})', time_range)
        if time_only_match:
            start_hour = time_only_match.group(1).zfill(2)
            start_min = time_only_match.group(2)
            end_hour = time_only_match.group(3).zfill(2)
            end_min = time_only_match.group(4)

            start_time = f'{start_hour}:{start_min}'
            end_time = f'{end_hour}:{end_min}'

            results.append((None, start_time, end_time))

    return results


def expand_day_range(start_day: str, end_day: str) -> list[str]:
    """Expand a day range into a list of individual days.

    Args:
        start_day: Starting day of the range
        end_day: Ending day of the range

    Returns:
        List of days in the range
    """
    day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

    # Handle case sensitivity
    start_day = start_day.title()
    end_day = end_day.title()

    start_index = -1
    end_index = -1

    for i, day in enumerate(day_order):
        if day.startswith(start_day):
            start_index = i
        if day.startswith(end_day):
            end_index = i

    if start_index == -1 or end_index == -1:
        raise ValueError(f'Could not parse day range: {start_day}-{end_day}')

    if end_index < start_index:
        end_index += 7  # Handle wrapping around the week

    result = []
    for i in range(start_index, end_index + 1):
        result.append(day_order[i % 7])

    return result
