from datetime import time
from unittest.mock import mock_open, patch

from src.scrapers.city_specific.turin import TurinScraper


def test_turin_scraper_initialization():
    """Test that the Turin scraper is properly initialized."""
    with patch('src.scrapers.base_scraper.requests.Session'):
        scraper = TurinScraper()

        assert scraper.base_url == 'http://www.comune.torino.it'
        assert scraper.city == 'Torino'
        assert scraper.ztl_page_path == '/trasporti/ztl'


def test_load_coordinates():
    """Test that the Turin scraper can load coordinates from JSON file."""
    # Mock JSON content for coordinates
    mock_json_content = """{
        "1": {
            "name": "ZTL Torino - Romana (21:00-07:30)",
            "id": "1",
            "center": [7.67976805488307, 45.07564171031928],
            "polygon": [[7.677949881927821, 45.07511049192392], [7.677933739327722, 45.07512241218467]]
        }
    }"""

    # Use patch to mock the open function when reading the coordinates file
    with (
        patch('builtins.open', mock_open(read_data=mock_json_content)),
        patch('src.scrapers.base_scraper.requests.Session'),
    ):
        scraper = TurinScraper()

        # Check that coordinates were loaded correctly
        assert len(scraper.ztl_coordinates) == 1
        assert '1' in scraper.ztl_coordinates
        assert scraper.ztl_coordinates['1']['name'] == 'ZTL Torino - Romana (21:00-07:30)'


def test_load_coordinates_file_not_found():
    """Test handling of missing coordinates file."""
    with (
        patch('builtins.open', side_effect=FileNotFoundError()),
        patch('src.scrapers.base_scraper.requests.Session'),
    ):
        scraper = TurinScraper()

        # Should have empty coordinates
        assert scraper.ztl_coordinates == {}


def test_load_coordinates_invalid_json():
    """Test handling of invalid JSON in coordinates file."""
    with (
        patch('builtins.open', mock_open(read_data='{"invalid": json')),
        patch('src.scrapers.base_scraper.requests.Session'),
    ):
        scraper = TurinScraper()

        # Should have empty coordinates
        assert scraper.ztl_coordinates == {}


def test_parse_zones():
    """Test that the Turin scraper can parse zones from coordinate data."""
    # Mock JSON content for coordinates
    mock_json_content = """{
        "1": {
            "name": "ZTL Torino - Romana (21:00-07:30)",
            "id": "1",
            "center": [7.67976805488307, 45.07564171031928],
            "polygon": [[7.677949881927821, 45.07511049192392], [7.677933739327722, 45.07512241218467]]
        },
        "2": {
            "name": "ZTL Torino - Centrale (07:30-10:30)",
            "id": "2",
            "center": [7.6854, 45.0705],
            "polygon": [[7.6853, 45.0703], [7.6855, 45.0707]]
        }
    }"""

    # Use patch to mock the open function when reading the coordinates file
    with (
        patch('builtins.open', mock_open(read_data=mock_json_content)),
        patch('src.scrapers.base_scraper.requests.Session'),
    ):
        scraper = TurinScraper()
        zones = scraper.parse_zones()

        # Check that zones were created correctly
        assert len(zones) == 2

        # Check first zone
        assert zones[0].id == 'turin-ztl-1'
        assert zones[0].name == 'ZTL Torino - Romana (21:00-07:30)'
        assert zones[0].city == 'Torino'
        assert len(zones[0].boundaries) == 2

        # Check for time restriction in the first zone
        assert len(zones[0].restrictions) == 1
        assert zones[0].restrictions[0].start_time == time(21, 0)
        assert zones[0].restrictions[0].end_time == time(7, 30)
        assert len(zones[0].restrictions[0].days) == 7  # All days of the week

        # Check second zone
        assert zones[1].id == 'turin-ztl-2'
        assert zones[1].name == 'ZTL Torino - Centrale (07:30-10:30)'
        assert len(zones[1].restrictions) == 1
        assert zones[1].restrictions[0].start_time == time(7, 30)
        assert zones[1].restrictions[0].end_time == time(10, 30)


def test_parse_zones_with_valentino():
    """Test parsing zones with Valentino ZTL."""
    mock_json_content = """{
        "3": {
            "name": "ZTL Torino - Valentino",
            "id": "3",
            "center": [7.6854, 45.0705],
            "polygon": [[7.6853, 45.0703], [7.6855, 45.0707]]
        }
    }"""

    with (
        patch('builtins.open', mock_open(read_data=mock_json_content)),
        patch('src.scrapers.base_scraper.requests.Session'),
    ):
        scraper = TurinScraper()
        zones = scraper.parse_zones()

        assert len(zones) == 1
        assert zones[0].id == 'turin-ztl-3'
        assert 'Valentino' in zones[0].name
        assert len(zones[0].restrictions) == 1
        assert zones[0].restrictions[0].start_time == time(0, 0)
        assert zones[0].restrictions[0].end_time == time(23, 59)


def test_parse_zones_with_time_in_name():
    """Test parsing zones with time information in the name but using default schedule.

    Note: Per implementation, if a zone doesn't match a known pattern (Romana, Valentino),
    it uses the ZTL Centrale schedule (07:30-10:30) and doesn't extract times from name.
    """
    mock_json_content = """{
        "4": {
            "name": "ZTL Torino - Custom Zone (14:30-18:45)",
            "id": "4",
            "center": [7.6854, 45.0705],
            "polygon": [[7.6853, 45.0703], [7.6855, 45.0707]]
        }
    }"""

    with (
        patch('builtins.open', mock_open(read_data=mock_json_content)),
        patch('src.scrapers.base_scraper.requests.Session'),
    ):
        scraper = TurinScraper()
        zones = scraper.parse_zones()

        assert len(zones) == 1
        assert zones[0].id == 'turin-ztl-4'
        assert len(zones[0].restrictions) == 1
        # In the current implementation, this uses the ZTL Centrale schedule
        assert zones[0].restrictions[0].start_time == time(7, 30)
        assert zones[0].restrictions[0].end_time == time(10, 30)
        # Days should be weekdays (Monday-Friday)
        assert len(zones[0].restrictions[0].days) == 5


def test_get_ztl_info():
    """Test the fixed ZTL information from Turin."""
    # Use patch to avoid actual network requests
    with (
        patch('builtins.open', mock_open(read_data='{}')),
        patch('src.scrapers.base_scraper.requests.Session'),
    ):
        scraper = TurinScraper()

        # Get the fixed ZTL info
        ztl_info = scraper._get_ztl_info()

        # Check that the information matches our fixed data
        assert 'ZTL Centrale' in ztl_info
        assert 'ZTL Romana' in ztl_info
        assert 'ZTL Valentino' in ztl_info
        assert 'Piazza Emanuele Filiberto' in ztl_info

        # Check specific schedule data
        assert ztl_info['ZTL Centrale']['Monday-Friday'] == '07:30-10:30'
        assert ztl_info['ZTL Romana']['Every day'] == '21:00-07:30'
        assert ztl_info['ZTL Valentino']['Every day'] == '00:00-23:59'


def test_expand_day_range_with_every_day():
    """Test expanding 'Every day' day range."""
    with (
        patch('builtins.open', mock_open(read_data='{}')),
        patch('src.scrapers.base_scraper.requests.Session'),
    ):
        scraper = TurinScraper()
        days = scraper._expand_day_range('Every day')

        assert days == ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']


def test_expand_day_range_with_unknown_format():
    """Test expanding unrecognized day range format."""
    with (
        patch('builtins.open', mock_open(read_data='{}')),
        patch('src.scrapers.base_scraper.requests.Session'),
    ):
        scraper = TurinScraper()
        days = scraper._expand_day_range('Weekdays')

        # Should default to weekdays
        assert days == ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']


def test_expand_day_range_with_invalid_days():
    """Test expanding day range with invalid day names."""
    with (
        patch('builtins.open', mock_open(read_data='{}')),
        patch('src.scrapers.base_scraper.requests.Session'),
    ):
        scraper = TurinScraper()
        days = scraper._expand_day_range('Invalid-Day')

        # Should default to weekdays
        assert days == ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
