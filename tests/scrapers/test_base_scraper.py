"""Tests for the base scraper functionality."""

from unittest.mock import MagicMock, patch

import pytest

from src.scrapers.base_scraper import BaseScraper


# Create a concrete implementation of BaseScraper for testing
class TestScraper(BaseScraper):
    """Concrete implementation of BaseScraper for testing."""

    def parse_zones(self):
        """Implementation of abstract method for testing."""
        return []


def test_base_scraper_initialization():
    """Test that the base scraper can be initialized with proper attributes."""
    scraper = TestScraper(base_url='https://example.com')

    assert scraper.base_url == 'https://example.com'
    assert hasattr(scraper, 'session')


def test_get_html_content():
    """Test that the scraper can fetch HTML content."""
    # Setup mock
    with patch('src.scrapers.base_scraper.requests.Session') as mock_session:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = '<html><body>Test Content</body></html>'
        mock_session_instance = MagicMock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance

        # Create scraper and fetch content
        scraper = TestScraper(base_url='https://example.com')
        content = scraper.get_html_content('/test-page')

        # Assertions
        assert content == '<html><body>Test Content</body></html>'
        mock_session_instance.get.assert_called_once_with('https://example.com/test-page')


def test_get_html_content_error_handling():
    """Test that the scraper handles errors when fetching content."""
    # Setup mock for request error
    with patch('src.scrapers.base_scraper.requests.Session') as mock_session:
        mock_session_instance = MagicMock()
        mock_session_instance.get.side_effect = Exception('Network error')
        mock_session.return_value = mock_session_instance

        # Create scraper and try to fetch content
        scraper = TestScraper(base_url='https://example.com')

        # Assertions - should raise an exception or return None
        with pytest.raises(Exception):  # noqa: B017
            scraper.get_html_content('/test-page')


def test_get_html_content_non_200_response():
    """Test that the scraper handles non-200 HTTP responses."""
    # Setup mock for non-200 response
    with patch('src.scrapers.base_scraper.requests.Session') as mock_session:
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = 'Not Found'
        mock_session_instance = MagicMock()
        mock_session_instance.get.return_value = mock_response
        mock_session.return_value = mock_session_instance

        # Create scraper and try to fetch content
        scraper = TestScraper(base_url='https://example.com')

        # Assertions - should raise an exception for non-200 status code
        with pytest.raises(Exception, match='Error fetching URL'):
            scraper.get_html_content('/not-found')


def test_base_scraper_abstract_method():
    """Test that the base scraper requires implementation of parse_zones method."""
    # Attempting to instantiate BaseScraper directly should raise TypeError
    with pytest.raises(TypeError):
        BaseScraper(base_url='https://example.com')
