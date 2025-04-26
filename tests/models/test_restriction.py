"""Tests for the Restriction class."""

from datetime import datetime

from src.models.restriction import Restriction


def test_restriction_initialization():
    """Test that a restriction can be properly initialized."""
    days = ['Monday', 'Tuesday', 'Wednesday']
    start_time = '08:00'
    end_time = '18:00'
    vehicle_types = ['Euro 0', 'Euro 1', 'Euro 2']

    restriction = Restriction(days=days, start_time=start_time, end_time=end_time, vehicle_types=vehicle_types)

    assert restriction.days == days
    assert restriction.start_time.hour == 8
    assert restriction.start_time.minute == 0
    assert restriction.end_time.hour == 18
    assert restriction.end_time.minute == 0
    assert restriction.vehicle_types == vehicle_types


def test_is_active_at():
    """Test that the restriction correctly determines if it's active at a given time."""
    restriction = Restriction(days=['Monday', 'Wednesday', 'Friday'], start_time='09:30', end_time='17:45')

    # Active: Wednesday at 10:00
    assert restriction.is_active_at(datetime(2023, 5, 10, 10, 0)) is True

    # Active: Wednesday exactly at start time
    assert restriction.is_active_at(datetime(2023, 5, 10, 9, 30)) is True

    # Active: Wednesday exactly at end time
    assert restriction.is_active_at(datetime(2023, 5, 10, 17, 45)) is True

    # Not active: Wednesday before hours
    assert restriction.is_active_at(datetime(2023, 5, 10, 9, 0)) is False

    # Not active: Wednesday after hours
    assert restriction.is_active_at(datetime(2023, 5, 10, 18, 0)) is False

    # Not active: Tuesday (wrong day)
    assert restriction.is_active_at(datetime(2023, 5, 9, 12, 0)) is False


def test_parse_time():
    """Test the _parse_time helper method."""
    restriction = Restriction(days=['Monday'], start_time='08:15', end_time='18:45')

    assert restriction.start_time.hour == 8
    assert restriction.start_time.minute == 15
    assert restriction.end_time.hour == 18
    assert restriction.end_time.minute == 45
