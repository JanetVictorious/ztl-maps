"""Tests for the Milan ZTL zone scraper."""

from datetime import datetime
from unittest.mock import patch

from src.scrapers.city_specific.milan import MilanScraper

# Mocked HTML content for testing
SAMPLE_MILAN_HTML = """
<html>
<body>
    <div class="ztl-info">
        <h2>Area C</h2>
        <p>Operating Hours: Monday-Friday 7:30-19:30</p>
        <div class="map-data" data-coordinates="9.1859,45.4654;9.1897,45.4675;9.1923,45.4662;9.1883,45.4641;9.1859,45.4654"></div>
    </div>
    <div class="ztl-info">
        <h2>Area B</h2>
        <p>Operating Hours: Monday-Friday 7:30-19:30, Saturday 10:00-18:00</p>
        <div class="map-data" data-coordinates="9.1700,45.4600;9.1800,45.4700;9.1900,45.4650;9.1750,45.4550;9.1700,45.4600"></div>
    </div>
</body>
</html>
"""


def test_milan_scraper_initialization():
    """Test that the Milan scraper is properly initialized."""
    with patch('src.scrapers.base_scraper.requests.Session'):
        scraper = MilanScraper()

        assert scraper.base_url == 'https://www.comune.milano.it'
        assert scraper.city == 'Milano'


def test_parse_zones():
    """Test parsing ZTL zones from HTML content."""
    # Setup mock to return sample HTML
    with patch('src.scrapers.city_specific.milan.MilanScraper.get_html_content') as mock_get_html:
        mock_get_html.return_value = SAMPLE_MILAN_HTML

        # Create scraper and parse zones
        scraper = MilanScraper()
        zones = scraper.parse_zones()

        # Assertions
        assert len(zones) == 2

        # Check first zone (Area C)
        assert zones[0].id == 'milano-area-c'
        assert zones[0].name == 'Area C'
        assert zones[0].city == 'Milano'
        assert len(zones[0].boundaries) == 5
        assert len(zones[0].restrictions) == 1

        # Check Area C restrictions
        assert len(zones[0].restrictions[0].days) == 5  # Monday-Friday
        assert 'Monday' in zones[0].restrictions[0].days
        assert 'Friday' in zones[0].restrictions[0].days
        assert zones[0].restrictions[0].start_time.hour == 7
        assert zones[0].restrictions[0].start_time.minute == 30
        assert zones[0].restrictions[0].end_time.hour == 19
        assert zones[0].restrictions[0].end_time.minute == 30

        # Check second zone (Area B)
        assert zones[1].id == 'milano-area-b'
        assert zones[1].name == 'Area B'
        assert len(zones[1].restrictions) == 2  # Weekday and Saturday restrictions


def test_is_active_calculation():
    """Test that the parsed zones correctly calculate active times."""
    # Setup mock to return sample HTML
    with patch('src.scrapers.city_specific.milan.MilanScraper.get_html_content', return_value=SAMPLE_MILAN_HTML):
        # Create scraper and parse zones
        scraper = MilanScraper()
        zones = scraper.parse_zones()

    # Wednesday at noon (should be active for both zones)
    wednesday_noon = datetime(2023, 5, 10, 12, 0)
    assert zones[0].is_active_at(wednesday_noon) is True  # Area C
    assert zones[1].is_active_at(wednesday_noon) is True  # Area B

    # Saturday at noon (should be active only for Area B)
    saturday_noon = datetime(2023, 5, 13, 12, 0)
    assert zones[0].is_active_at(saturday_noon) is False  # Area C
    assert zones[1].is_active_at(saturday_noon) is True  # Area B

    # Sunday (should be inactive for both)
    sunday = datetime(2023, 5, 14, 12, 0)
    assert zones[0].is_active_at(sunday) is False
    assert zones[1].is_active_at(sunday) is False
