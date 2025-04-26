"""Tests for scraper utility functions."""

import json

from src.scrapers.utils import (
    expand_day_range,
    extract_coordinates_from_geojson,
    extract_time_ranges,
    parse_coordinates,
)


def test_parse_coordinates_semicolon_format():
    """Test parsing coordinates in semicolon format."""
    coords = '9.1859,45.4654;9.1897,45.4675;9.1923,45.4662'
    result = parse_coordinates(coords, 'semicolon')

    assert len(result) == 3
    assert result[0] == [9.1859, 45.4654]
    assert result[1] == [9.1897, 45.4675]
    assert result[2] == [9.1923, 45.4662]


def test_parse_coordinates_brackets_format():
    """Test parsing coordinates in brackets format."""
    coords = '[[9.1859, 45.4654], [9.1897, 45.4675], [9.1923, 45.4662]]'
    result = parse_coordinates(coords, 'brackets')

    assert len(result) == 3
    assert result[0] == [9.1859, 45.4654]
    assert result[1] == [9.1897, 45.4675]
    assert result[2] == [9.1923, 45.4662]


def test_parse_coordinates_space_format():
    """Test parsing coordinates in space format."""
    coords = '9.1859 45.4654 9.1897 45.4675 9.1923 45.4662'
    result = parse_coordinates(coords, 'space')

    assert len(result) == 3
    assert result[0] == [9.1859, 45.4654]
    assert result[1] == [9.1897, 45.4675]
    assert result[2] == [9.1923, 45.4662]


def test_parse_coordinates_geojson_format():
    """Test parsing coordinates from GeoJSON format."""
    geojson = {
        'type': 'Polygon',
        'coordinates': [
            [[9.1859, 45.4654], [9.1897, 45.4675], [9.1923, 45.4662], [9.1883, 45.4641], [9.1859, 45.4654]]
        ],
    }

    # Test with dict input
    result = parse_coordinates(geojson, 'geojson')
    assert len(result) == 5
    assert result[0] == [9.1859, 45.4654]

    # Test with string input
    geojson_str = json.dumps(geojson)
    result = parse_coordinates(geojson_str, 'geojson')
    assert len(result) == 5
    assert result[0] == [9.1859, 45.4654]


def test_extract_coordinates_from_geojson():
    """Test extracting coordinates from GeoJSON objects."""
    # Test Polygon geometry
    polygon = {
        'type': 'Polygon',
        'coordinates': [[[9.1859, 45.4654], [9.1897, 45.4675], [9.1923, 45.4662], [9.1859, 45.4654]]],
    }
    result = extract_coordinates_from_geojson(polygon)
    assert len(result) == 4

    # Test Point geometry
    point = {'type': 'Point', 'coordinates': [9.1859, 45.4654]}
    result = extract_coordinates_from_geojson(point)
    assert len(result) == 1
    assert result[0] == [9.1859, 45.4654]

    # Test Feature
    feature = {
        'type': 'Feature',
        'geometry': {'type': 'Point', 'coordinates': [9.1859, 45.4654]},
        'properties': {'name': 'Test Point'},
    }
    result = extract_coordinates_from_geojson(feature)
    assert len(result) == 1
    assert result[0] == [9.1859, 45.4654]

    # Test FeatureCollection
    collection = {
        'type': 'FeatureCollection',
        'features': [
            {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [9.1859, 45.4654]}},
            {'type': 'Feature', 'geometry': {'type': 'Point', 'coordinates': [9.1897, 45.4675]}},
        ],
    }
    result = extract_coordinates_from_geojson(collection)
    assert len(result) == 2


def test_extract_time_ranges():
    """Test extracting time ranges from text."""
    # Test day range pattern
    text = 'Monday-Friday 7:30-19:30'
    result = extract_time_ranges(text)
    assert len(result) == 1
    days, start_time, end_time = result[0]
    assert days == ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    assert start_time == '07:30'
    assert end_time == '19:30'

    # Test single day pattern
    text = 'Saturday 10:00-18:00'
    result = extract_time_ranges(text)
    assert len(result) == 1
    days, start_time, end_time = result[0]
    assert days == ['Saturday']
    assert start_time == '10:00'
    assert end_time == '18:00'

    # Test time-only pattern
    text = '7:30-19:30'
    result = extract_time_ranges(text)
    assert len(result) == 1
    days, start_time, end_time = result[0]
    assert days is None
    assert start_time == '07:30'
    assert end_time == '19:30'

    # Test multiple patterns
    text = 'Monday-Friday 7:30-19:30, Saturday 10:00-18:00'
    result = extract_time_ranges(text)
    assert len(result) == 2

    days1, start_time1, end_time1 = result[0]
    assert days1 == ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    assert start_time1 == '07:30'
    assert end_time1 == '19:30'

    days2, start_time2, end_time2 = result[1]
    assert days2 == ['Saturday']
    assert start_time2 == '10:00'
    assert end_time2 == '18:00'


def test_expand_day_range():
    """Test expanding day ranges into lists of days."""
    # Test Monday to Friday
    result = expand_day_range('Monday', 'Friday')
    assert result == ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

    # Test weekend days
    result = expand_day_range('Saturday', 'Sunday')
    assert result == ['Saturday', 'Sunday']

    # Test single day (start and end are the same)
    result = expand_day_range('Wednesday', 'Wednesday')
    assert result == ['Wednesday']

    # Test case insensitivity
    result = expand_day_range('monday', 'friday')
    assert result == ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

    # Test abbreviated days
    result = expand_day_range('Mon', 'Fri')
    assert result == ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

    # Test wrap around week (Friday to Monday)
    result = expand_day_range('Friday', 'Monday')
    assert result == ['Friday', 'Saturday', 'Sunday', 'Monday']
