"""Tests for the Florence ZTL zone scraper."""

from datetime import datetime
from unittest.mock import patch

from src.scrapers.city_specific.florence import FlorenceScraper

# Mocked HTML content for testing
SAMPLE_FLORENCE_HTML = """
<html>
<body>
    <div class="ztl-info">
        <h2>ZTL Centro Storico</h2>
        <p>Operating Hours: Monday-Friday 7:30-20:00, Saturday 10:00-16:00</p>
        <div class="map-data" data-coordinates="11.2558,43.7764;11.2615,43.7781;11.2631,43.7755;11.2592,43.7728;11.2558,43.7764"></div>
    </div>
    <div class="ztl-info">
        <h2>ZTL Settore A</h2>
        <p>Operating Hours: Monday-Friday 8:00-18:30</p>
        <div class="map-data" data-coordinates="11.2500,43.7700;11.2550,43.7750;11.2600,43.7730;11.2540,43.7680;11.2500,43.7700"></div>
    </div>
</body>
</html>
"""


def test_florence_scraper_initialization():
    """Test that the Florence scraper is properly initialized."""
    with patch('src.scrapers.base_scraper.requests.Session'):
        scraper = FlorenceScraper()

        assert scraper.base_url == 'https://www.comune.fi.it'
        assert scraper.city == 'Firenze'


def test_parse_zones():
    """Test parsing ZTL zones from HTML content."""
    # Setup mock to return sample HTML
    with patch('src.scrapers.city_specific.florence.FlorenceScraper.get_html_content') as mock_get_html:
        mock_get_html.return_value = SAMPLE_FLORENCE_HTML

        # Create scraper and parse zones
        scraper = FlorenceScraper()
        zones = scraper.parse_zones()

        # Assertions
        assert len(zones) == 2

        # Check first zone (ZTL Centro Storico)
        assert zones[0].id == 'firenze-ztl-centro-storico'
        assert zones[0].name == 'ZTL Centro Storico'
        assert zones[0].city == 'Firenze'
        assert len(zones[0].boundaries) == 5
        assert len(zones[0].restrictions) == 2

        # Check ZTL Centro Storico weekday restrictions
        assert len(zones[0].restrictions[0].days) == 5  # Monday-Friday
        assert 'Monday' in zones[0].restrictions[0].days
        assert 'Friday' in zones[0].restrictions[0].days
        assert zones[0].restrictions[0].start_time.hour == 7
        assert zones[0].restrictions[0].start_time.minute == 30
        assert zones[0].restrictions[0].end_time.hour == 20
        assert zones[0].restrictions[0].end_time.minute == 0

        # Check ZTL Centro Storico Saturday restrictions
        assert len(zones[0].restrictions[1].days) == 1  # Saturday only
        assert 'Saturday' in zones[0].restrictions[1].days
        assert zones[0].restrictions[1].start_time.hour == 10
        assert zones[0].restrictions[1].start_time.minute == 0
        assert zones[0].restrictions[1].end_time.hour == 16
        assert zones[0].restrictions[1].end_time.minute == 0

        # Check second zone (ZTL Settore A)
        assert zones[1].id == 'firenze-ztl-settore-a'
        assert zones[1].name == 'ZTL Settore A'
        assert len(zones[1].restrictions) == 1  # Only weekday restrictions


def test_is_active_calculation():
    """Test that the parsed zones correctly calculate active times."""
    # Setup mock to return sample HTML
    with patch(
        'src.scrapers.city_specific.florence.FlorenceScraper.get_html_content', return_value=SAMPLE_FLORENCE_HTML
    ):
        # Create scraper and parse zones
        scraper = FlorenceScraper()
        zones = scraper.parse_zones()

    # Wednesday at noon (should be active for both zones)
    wednesday_noon = datetime(2023, 5, 10, 12, 0)
    assert zones[0].is_active_at(wednesday_noon) is True  # ZTL Centro Storico
    assert zones[1].is_active_at(wednesday_noon) is True  # ZTL Settore A

    # Saturday at noon (should be active only for ZTL Centro Storico)
    saturday_noon = datetime(2023, 5, 13, 12, 0)
    assert zones[0].is_active_at(saturday_noon) is True  # ZTL Centro Storico
    assert zones[1].is_active_at(saturday_noon) is False  # ZTL Settore A

    # Sunday (should be inactive for both)
    sunday = datetime(2023, 5, 14, 12, 0)
    assert zones[0].is_active_at(sunday) is False
    assert zones[1].is_active_at(sunday) is False
