"""Scraper for Turin ZTL zones."""

import json
import re
from pathlib import Path
from typing import Any

from src.models.restriction import Restriction
from src.models.zone import Zone
from src.scrapers.base_scraper import BaseScraper


class TurinScraper(BaseScraper):
    """Scraper for Turin ZTL zones."""

    def __init__(self):
        """Initialize the Turin scraper with the appropriate URL."""
        super().__init__(base_url='http://www.comune.torino.it')
        self.city = 'Torino'
        self.ztl_page_path = '/trasporti/ztl'
        self.ztl_coordinates: dict[str, Any] = {}
        self._load_coordinates()

    def _load_coordinates(self) -> None:
        """Load ZTL zone coordinates from JSON file."""
        # Find the project root directory
        project_root = Path(__file__).parent.parent.parent.parent
        json_path = project_root / 'src' / 'data_storage' / 'cities' / 'turin.json'
        try:
            with open(json_path, encoding='utf-8') as f:
                json_content = f.read()
                if json_content:
                    self.ztl_coordinates = json.loads(json_content)
        except (FileNotFoundError, json.JSONDecodeError):
            # Fallback to empty dict if file not found or invalid
            self.ztl_coordinates = {}

    def _get_ztl_info(self) -> dict[str, dict[str, str]]:
        """Extract ZTL information from the city website.

        Returns:
            Dictionary mapping ZTL names to operating hours information
        """
        # Based on the fixed schedule information from the Turin website
        ztl_info = {
            'ZTL Centrale': {'Monday-Friday': '07:30-10:30'},
            'ZTL Romana': {'Every day': '21:00-07:30'},
            'Piazza Emanuele Filiberto': {'Every day': '19:30-07:30'},
            'ZTL Valentino': {'Every day': '00:00-23:59'},
        }

        return ztl_info

    def _parse_restriction(self, day_range: str, time_range: str) -> list[Restriction]:
        """Parse restriction from day range and time range.

        Args:
            day_range: String with day range (e.g., "Monday-Friday")
            time_range: String with time range (e.g., "07:30-19:00")

        Returns:
            List of Restriction objects
        """
        restrictions = []

        # Parse day range
        days = self._expand_day_range(day_range)

        # Create restriction with the time range
        start_time, end_time = time_range.split('-')
        restriction = Restriction(days=days, start_time=start_time, end_time=end_time)
        restrictions.append(restriction)

        return restrictions

    def _expand_day_range(self, day_range: str) -> list[str]:
        """Expand a day range into a list of individual days.

        Args:
            day_range: String with day range (e.g., "Monday-Friday")

        Returns:
            List of day names
        """
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        # Handle hyphenated ranges like "Monday-Friday"
        if '-' in day_range:
            start_day, end_day = day_range.split('-')

            # Find indices of start and end days
            try:
                start_index = day_order.index(start_day)
                end_index = day_order.index(end_day)
                return day_order[start_index : end_index + 1]
            except ValueError:
                # Default to weekdays if days not recognized
                return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

        # Handle special case for "Every day" or "Monday-Sunday"
        if day_range == 'Every day':
            return day_order

        # Default to weekdays if format not recognized
        return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

    def parse_zones(self) -> list[Zone]:
        """Parse zones from coordinates and schedule data.

        Returns:
            List of Zone objects representing Turin's ZTL zones
        """
        zones = []

        # Get ZTL info with fixed schedules
        ztl_info = self._get_ztl_info()

        for zone_id, zone_data in self.ztl_coordinates.items():
            # Extract name and boundaries
            name = zone_data.get('name', f'ZTL Torino - Zone {zone_id}')
            boundaries = zone_data.get('polygon', [])

            # Create zone
            zone = Zone(id=f'turin-ztl-{zone_id}', name=name, city=self.city, boundaries=boundaries)

            # Determine which ZTL schedule to apply based on the zone name
            if 'Romana' in name or 'romana' in name:
                # Apply ZTL Romana schedule
                for day_range, time_range in ztl_info['ZTL Romana'].items():
                    restrictions = self._parse_restriction(day_range, time_range)
                    for restriction in restrictions:
                        zone.add_restriction(restriction)
            elif 'Valentino' in name or 'valentino' in name:
                # Apply ZTL Valentino schedule
                for day_range, time_range in ztl_info['ZTL Valentino'].items():
                    restrictions = self._parse_restriction(day_range, time_range)
                    for restriction in restrictions:
                        zone.add_restriction(restriction)
            else:
                # Default to ZTL Centrale schedule for other zones
                for day_range, time_range in ztl_info['ZTL Centrale'].items():
                    restrictions = self._parse_restriction(day_range, time_range)
                    for restriction in restrictions:
                        zone.add_restriction(restriction)

            # If still no restrictions, try to extract from name as fallback
            if not zone.restrictions:
                time_match = re.search(r'\((\d{2}:\d{2})-(\d{2}:\d{2})\)', name)
                if time_match:
                    start_time = time_match.group(1)
                    end_time = time_match.group(2)

                    # Create restriction - assume all days by default
                    restriction = Restriction(
                        days=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
                        start_time=start_time,
                        end_time=end_time,
                    )
                    zone.add_restriction(restriction)

            zones.append(zone)

        return zones
