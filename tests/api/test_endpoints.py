"""Tests for API endpoints."""

from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.api.endpoints import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def mock_city():
    """Create a mock city with zones for testing."""
    city = MagicMock()
    city.name = 'Milano'
    city.country = 'Italy'

    zone1 = MagicMock()
    zone1.id = 'milano-area-c'
    zone1.name = 'Area C'
    zone1.city = 'Milano'
    zone1.is_active_at.return_value = True

    zone2 = MagicMock()
    zone2.id = 'milano-area-b'
    zone2.name = 'Area B'
    zone2.city = 'Milano'
    zone2.is_active_at.return_value = False

    city.zones = [zone1, zone2]
    return city


def test_get_cities(client):
    """Test the GET /cities endpoint."""
    # Mock the data access layer
    with patch('src.api.endpoints.get_all_cities') as mock_get_all_cities:
        mock_get_all_cities.return_value = [
            {'name': 'Milano', 'country': 'Italy'},
            {'name': 'Roma', 'country': 'Italy'},
        ]

        # Call the endpoint
        response = client.get('/cities')

        # Check response
        assert response.status_code == 200
        assert response.json() == [{'name': 'Milano', 'country': 'Italy'}, {'name': 'Roma', 'country': 'Italy'}]
        mock_get_all_cities.assert_called_once()


def test_get_city(client, mock_city):
    """Test the GET /cities/{city_name} endpoint."""
    # Mock the data access layer
    with patch('src.api.endpoints.load_city') as mock_load_city:
        mock_load_city.return_value = mock_city

        # Call the endpoint
        response = client.get('/cities/Milano')

        # Check response
        assert response.status_code == 200
        assert response.json()['name'] == 'Milano'
        assert response.json()['country'] == 'Italy'
        assert len(response.json()['zones']) == 2
        mock_load_city.assert_called_once_with('Milano')


def test_get_city_not_found(client):
    """Test the GET /cities/{city_name} endpoint with a non-existent city."""
    # Mock the data access layer
    with patch('src.api.endpoints.load_city') as mock_load_city:
        mock_load_city.return_value = None

        # Call the endpoint
        response = client.get('/cities/NonExistentCity')

        # Check response
        assert response.status_code == 404
        assert 'detail' in response.json()
        mock_load_city.assert_called_once_with('NonExistentCity')


def test_get_active_zones(client, mock_city):
    """Test the GET /cities/{city_name}/active-zones endpoint."""
    # Mock the data access layer
    with (
        patch('src.api.endpoints.load_city') as mock_load_city,
        patch('src.api.endpoints.datetime') as mock_datetime,
    ):
        mock_load_city.return_value = mock_city
        test_datetime = datetime(2023, 5, 10, 12, 0)  # Wednesday at noon
        mock_datetime.now.return_value = test_datetime

        # Call the endpoint
        response = client.get('/cities/Milano/active-zones')

        # Check response
        assert response.status_code == 200
        active_zones = response.json()
        assert len(active_zones) == 1
        assert active_zones[0]['name'] == 'Area C'
        mock_load_city.assert_called_once_with('Milano')
        mock_city.zones[0].is_active_at.assert_called_with(test_datetime)
        mock_city.zones[1].is_active_at.assert_called_with(test_datetime)
