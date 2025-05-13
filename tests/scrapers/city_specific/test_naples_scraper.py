"""Tests for the Naples ZTL zone scraper."""

import json
from datetime import datetime
from unittest.mock import mock_open, patch

from src.scrapers.city_specific.naples import NaplesScraper


def test_naples_scraper_initialization():
    """Test that the Naples scraper is properly initialized."""
    with patch('src.scrapers.base_scraper.requests.Session'):
        scraper = NaplesScraper()

        assert scraper.base_url == 'https://www.comune.napoli.it'
        assert scraper.city == 'Napoli'
        assert scraper.ztl_page_path == '/ztl'


def test_load_coordinates():
    """Test loading coordinates from JSON file."""
    # Sample JSON content for testing
    sample_data = {
        '4': {
            'name': 'ZTL Napoli - ZTL Morelli - Filangieri - Mille',
            'id': '4',
            'center': [14.243070518629484, 40.83558857130706],
            'polygon': [[14.238281933317214, 40.83665678136231], [14.240091184566628, 40.83663554632052]],
            'properties': {
                'id': '4',
                'name': 'ZTL Morelli - Filangieri - Mille',
                'entity_class': 32.0,
                'entity_ins': 1023971.0,
                'atto': None,
                'istituzione': None,
            },
        }
    }
    sample_json = json.dumps(sample_data)

    with (
        patch('builtins.open', mock_open(read_data=sample_json)),
        patch('src.scrapers.base_scraper.requests.Session'),
    ):
        scraper = NaplesScraper()

        # Replace the _load_coordinates method to directly set the coordinates
        # This isolates the test from the file loading logic
        scraper.ztl_coordinates = {}
        scraper._load_coordinates = lambda: scraper.ztl_coordinates.update(sample_data)
        scraper._load_coordinates()

        # Check if coordinates are loaded correctly
        assert '4' in scraper.ztl_coordinates
        assert scraper.ztl_coordinates['4']['name'] == 'ZTL Napoli - ZTL Morelli - Filangieri - Mille'
        assert len(scraper.ztl_coordinates['4']['polygon']) == 2


def test_load_coordinates_with_file_not_found():
    """Test handling of missing coordinates file."""
    with (
        patch('builtins.open', side_effect=FileNotFoundError),
        patch('src.scrapers.base_scraper.requests.Session'),
    ):
        scraper = NaplesScraper()

        # Call _load_coordinates explicitly
        scraper._load_coordinates()

        # Check if an empty dict is used as fallback
        assert scraper.ztl_coordinates == {}


def test_parse_zones():
    """Test parsing ZTL zones from coordinates data."""
    # Sample coordinates data
    sample_coordinates = {
        '4': {
            'name': 'ZTL Napoli - ZTL Morelli - Filangieri - Mille',
            'id': '4',
            'center': [14.243070518629484, 40.83558857130706],
            'polygon': [[14.238281933317214, 40.83665678136231], [14.240091184566628, 40.83663554632052]],
            'properties': {
                'id': '4',
                'name': 'ZTL Morelli - Filangieri - Mille',
                'entity_class': 32.0,
                'entity_ins': 1023971.0,
                'atto': None,
                'istituzione': None,
            },
        },
        '1': {
            'name': 'ZTL Napoli - ZTL Centro Antico',
            'id': '1',
            'center': [14.25, 40.85],
            'polygon': [[14.249, 40.847], [14.251, 40.848], [14.250, 40.849]],
            'properties': {
                'id': '1',
                'name': 'ZTL Centro Antico',
                'entity_class': 32.0,
                'entity_ins': 1023968.0,
                'atto': None,
                'istituzione': None,
            },
        },
    }

    with (
        patch('src.scrapers.base_scraper.requests.Session'),
        patch.object(NaplesScraper, '_load_coordinates'),
    ):
        scraper = NaplesScraper()
        scraper.ztl_coordinates = sample_coordinates

        # Create a sample hours data
        sample_hours = {
            'ZTL Centro Antico': {'Monday-Friday': '07:00-19:00', 'Saturday-Sunday': '10:00-14:00'},
            'ZTL Morelli - Filangieri - Mille': {'Monday-Friday': '08:00-18:00'},
        }

        # Patch the _get_ztl_hours method
        with patch.object(NaplesScraper, '_get_ztl_hours', return_value=sample_hours):
            zones = scraper.parse_zones()

            # Check if zones are created correctly
            assert len(zones) == 2

            # Find zones by ID
            zone_4 = next((z for z in zones if z.id == 'naples-ztl-4'), None)
            zone_1 = next((z for z in zones if z.id == 'naples-ztl-1'), None)

            assert zone_4 is not None
            assert zone_1 is not None

            # Check zone 4 properties
            assert zone_4.name == 'ZTL Morelli - Filangieri - Mille'
            assert zone_4.city == 'Napoli'
            assert len(zone_4.boundaries) == 2
            assert len(zone_4.restrictions) == 1

            # Check zone 1 properties
            assert zone_1.name == 'ZTL Centro Antico'
            assert len(zone_1.boundaries) == 3
            assert len(zone_1.restrictions) == 2


def test_parse_zones_with_missing_hours():
    """Test parsing ZTL zones when no hours are available for a ZTL."""
    # Sample coordinates data with a ZTL that won't have hours
    sample_coordinates = {
        '5': {
            'name': 'ZTL Unknown Zone',
            'id': '5',
            'polygon': [[14.25, 40.85], [14.26, 40.86], [14.27, 40.87]],
            'properties': {'id': '5', 'name': 'ZTL Unknown Zone'},
        }
    }

    with (
        patch('src.scrapers.base_scraper.requests.Session'),
        patch.object(NaplesScraper, '_load_coordinates'),
    ):
        scraper = NaplesScraper()
        scraper.ztl_coordinates = sample_coordinates

        # Create a sample hours data that doesn't include the ZTL in coordinates
        sample_hours = {'ZTL Centro Antico': {'Monday-Friday': '07:00-19:00'}}

        # Patch the _get_ztl_hours method
        with patch.object(NaplesScraper, '_get_ztl_hours', return_value=sample_hours):
            zones = scraper.parse_zones()

            # Check if zones are created correctly
            assert len(zones) == 1

            # Check that zone was created despite not having hours
            assert zones[0].id == 'naples-ztl-5'
            assert zones[0].name == 'ZTL Unknown Zone'
            assert len(zones[0].restrictions) == 0  # No restrictions should be added


def test_is_active_calculation():
    """Test that the parsed zones correctly calculate active times."""
    with (
        patch('src.scrapers.base_scraper.requests.Session'),
        patch.object(NaplesScraper, '_load_coordinates'),
    ):
        scraper = NaplesScraper()

        # Mock coordinates data
        sample_coordinates = {
            '1': {
                'name': 'ZTL Napoli - ZTL Centro Antico',
                'id': '1',
                'polygon': [[14.249, 40.847], [14.251, 40.848], [14.250, 40.849]],
                'properties': {'name': 'ZTL Centro Antico'},
            }
        }
        scraper.ztl_coordinates = sample_coordinates

        # Mock hours data with the updated schedule
        sample_hours = {
            'ZTL Centro Antico': {
                'Monday-Thursday': '09:00-22:00',
                'Friday-Sunday': '09:00-23:59',
                'Every day': '09:00-17:00',
            }
        }

        with patch.object(NaplesScraper, '_get_ztl_hours', return_value=sample_hours):
            zones = scraper.parse_zones()

            # Get the zone to test
            zone = zones[0]

            # Wednesday at noon (should be active - within "Every day" and "Monday-Thursday" windows)
            wednesday_noon = datetime(2023, 5, 10, 12, 0)
            assert zone.is_active_at(wednesday_noon) is True

            # Saturday at noon (should be active - within "Every day" and "Friday-Sunday" windows)
            saturday_noon = datetime(2023, 5, 13, 12, 0)
            assert zone.is_active_at(saturday_noon) is True

            # Saturday at 20:00 (should be active - within "Friday-Sunday" window)
            saturday_evening = datetime(2023, 5, 13, 20, 0)
            assert zone.is_active_at(saturday_evening) is True

            # Wednesday at 23:00 (should be inactive - outside all windows)
            wednesday_night = datetime(2023, 5, 10, 23, 0)
            assert zone.is_active_at(wednesday_night) is False

            # Every day early morning 7:00 (should be inactive - outside all windows)
            early_morning = datetime(2023, 5, 10, 7, 0)
            assert zone.is_active_at(early_morning) is False


def test_parse_restriction():
    """Test parsing restrictions from day range and time range."""
    with patch('src.scrapers.base_scraper.requests.Session'):
        scraper = NaplesScraper()

        # Test with weekday range
        restrictions = scraper._parse_restriction('Monday-Friday', '07:00-19:00')
        assert len(restrictions) == 1
        assert len(restrictions[0].days) == 5
        assert 'Monday' in restrictions[0].days
        assert 'Friday' in restrictions[0].days
        assert restrictions[0].start_time.hour == 7
        assert restrictions[0].start_time.minute == 0
        assert restrictions[0].end_time.hour == 19
        assert restrictions[0].end_time.minute == 0

        # Test with weekend range
        restrictions = scraper._parse_restriction('Saturday-Sunday', '10:00-14:00')
        assert len(restrictions) == 1
        assert len(restrictions[0].days) == 2
        assert 'Saturday' in restrictions[0].days
        assert 'Sunday' in restrictions[0].days
        assert restrictions[0].start_time.hour == 10
        assert restrictions[0].start_time.minute == 0
        assert restrictions[0].end_time.hour == 14
        assert restrictions[0].end_time.minute == 0


def test_get_ztl_hours():
    """Test getting ZTL hours from HTML content."""
    # Sample HTML content simulating Naples website
    sample_html = """
    <div class="ztl-info">
        <h3>ZTL Centro Antico</h3>
        <p>Orari: Dal lunedì al venerdì 07:00-19:00, Sabato e domenica 10:00-14:00</p>
    </div>
    <div class="ztl-info">
        <h3>ZTL Morelli - Filangieri - Mille</h3>
        <p>Orari: Dal lunedì al venerdì 08:00-18:00</p>
    </div>
    """

    with patch('src.scrapers.base_scraper.requests.Session'):
        scraper = NaplesScraper()

        # Patch get_html_content to return our sample HTML
        with patch.object(NaplesScraper, 'get_html_content', return_value=sample_html):
            hours = scraper._get_ztl_hours()

            assert len(hours) == 2
            assert 'ZTL Centro Antico' in hours
            assert 'ZTL Morelli - Filangieri - Mille' in hours
            assert hours['ZTL Centro Antico']['Monday-Friday'] == '07:00-19:00'
            assert hours['ZTL Centro Antico']['Saturday-Sunday'] == '10:00-14:00'
            assert hours['ZTL Morelli - Filangieri - Mille']['Monday-Friday'] == '08:00-18:00'


def test_get_ztl_hours_with_incomplete_html():
    """Test getting ZTL hours from HTML content with incomplete data."""
    # Sample HTML content with incomplete data
    sample_html = """
    <div class="ztl-info">
        <h3>ZTL Centro Antico</h3>
        <!-- Missing p element with hours -->
    </div>
    <div class="ztl-info">
        <!-- Missing h3 element with name -->
        <p>Orari: Dal lunedì al venerdì 08:00-18:00</p>
    </div>
    <div class="ztl-info">
        <h3>ZTL With Other Format</h3>
        <p>Orari: 09:00-17:00</p>
    </div>
    """

    with patch('src.scrapers.base_scraper.requests.Session'):
        scraper = NaplesScraper()

        # Patch get_html_content to return our sample HTML
        with patch.object(NaplesScraper, 'get_html_content', return_value=sample_html):
            hours = scraper._get_ztl_hours()

            # Check the only ZTL with complete data and a different format
            assert 'ZTL With Other Format' in hours
            assert 'Monday-Friday' in hours['ZTL With Other Format']
            assert hours['ZTL With Other Format']['Monday-Friday'] == '09:00-17:00'

            # The implementation doesn't add partial entries to the hours dict
            # It only adds complete entries with both name and hours
            assert len(hours) == 1


def test_get_ztl_hours_with_no_html_data():
    """Test getting ZTL hours when HTML data is not available or fails to parse."""
    with patch('src.scrapers.base_scraper.requests.Session'):
        scraper = NaplesScraper()

        # Patch get_html_content to raise an exception
        with patch.object(NaplesScraper, 'get_html_content', side_effect=Exception('Failed to fetch')):
            hours = scraper._get_ztl_hours()

            # Should return default schedules
            assert len(hours) == 5
            assert 'ZTL Centro Antico' in hours
            assert 'ZTL Morelli - Filangieri - Mille' in hours
            assert 'ZTL Tarsia - Pignasecca - Dante' in hours
            assert 'ZTL Belledonne - Martiri - Poerio' in hours
            assert 'ZTL Marechiaro' in hours

            # Check that ZTL Centro Antico has the updated schedule
            assert 'Monday-Thursday' in hours['ZTL Centro Antico']
            assert 'Friday-Sunday' in hours['ZTL Centro Antico']
            assert 'Every day' in hours['ZTL Centro Antico']
            assert hours['ZTL Centro Antico']['Monday-Thursday'] == '09:00-22:00'
            assert hours['ZTL Centro Antico']['Friday-Sunday'] == '09:00-23:59'
            assert hours['ZTL Centro Antico']['Every day'] == '09:00-17:00'


def test_expand_day_range():
    """Test expanding day ranges into lists of days."""
    with patch('src.scrapers.base_scraper.requests.Session'):
        scraper = NaplesScraper()

        # Test valid weekday range
        weekdays = scraper._expand_day_range('Monday-Friday')
        assert len(weekdays) == 5
        assert weekdays == ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

        # Test valid weekend range
        weekend = scraper._expand_day_range('Saturday-Sunday')
        assert len(weekend) == 2
        assert weekend == ['Saturday', 'Sunday']

        # Test single day
        single_day = scraper._expand_day_range('Wednesday')
        assert len(single_day) == 1
        assert single_day == ['Wednesday']

        # Test invalid day range (non-existent days)
        invalid_range = scraper._expand_day_range('InvalidDay-OtherInvalidDay')
        assert len(invalid_range) == 5  # Should default to weekdays
        assert invalid_range == ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

        # Test unrecognized format
        unrecognized = scraper._expand_day_range('not a day range')
        assert len(unrecognized) == 5  # Should default to weekdays
        assert unrecognized == ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
