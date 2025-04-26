"""Data model for time-based and vehicle-type restrictions."""

from datetime import time


class Restriction:  # pylint: disable=too-few-public-methods
    """Time-based restriction for a zone."""

    def __init__(self, days, start_time, end_time, vehicle_types=None):
        """Initialize a restriction.

        Args:
            days: List of days when the restriction is active (e.g., ["Monday", "Tuesday"])
            start_time: Start time as string in format "HH:MM"
            end_time: End time as string in format "HH:MM"
            vehicle_types: Optional list of vehicle types affected by this restriction
        """
        self.days = days
        self.start_time = self._parse_time(start_time)
        self.end_time = self._parse_time(end_time)
        self.vehicle_types = vehicle_types or []

    def _parse_time(self, time_str):
        """Parse a time string in format 'HH:MM' to a time object."""
        hours, minutes = map(int, time_str.split(':'))
        return time(hours, minutes)

    def is_active_at(self, dt):
        """Check if this restriction is active at the given datetime.

        Args:
            dt: A datetime object to check

        Returns:
            bool: True if the restriction is active, False otherwise
        """
        # Check if the day matches
        day_name = dt.strftime('%A')
        if day_name not in self.days:
            return False

        # Check if the time is within the restriction window
        current_time = dt.time()
        return self.start_time <= current_time <= self.end_time
