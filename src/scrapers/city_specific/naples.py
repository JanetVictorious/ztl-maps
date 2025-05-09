"""Scraper for Naples ZTL zones."""

import json
import re
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from src.models.restriction import Restriction
from src.models.zone import Zone
from src.scrapers.base_scraper import BaseScraper


class NaplesScraper(BaseScraper):
    """Scraper for Naples ZTL zones."""

    def __init__(self):
        """Initialize the Naples scraper with the appropriate URL."""
        super().__init__(base_url='https://www.comune.napoli.it')
        self.city = 'Napoli'
        self.ztl_page_path = '/ztl'
        self.ztl_coordinates: dict[str, Any] = {}
        self._load_coordinates()

    def _load_coordinates(self) -> None:
        """Load ZTL zone coordinates from JSON file."""
        json_path = Path(__file__).parent / 'ztl_coordinates' / 'naples.json'
        try:
            with open(json_path, encoding='utf-8') as f:
                json_content = f.read()
                if json_content:
                    self.ztl_coordinates = json.loads(json_content)
        except (FileNotFoundError, json.JSONDecodeError):
            # Fallback to empty dict if file not found or invalid
            self.ztl_coordinates = {}

    def parse_zones(self) -> list[Zone]:
        """Parse zones from coordinates and schedule data.

        Returns:
            List of Zone objects representing Naples' ZTL zones
        """
        zones = []

        # Get ZTL schedules from HTML or other sources
        ztl_hours = self._get_ztl_hours()

        # Create zones from coordinates and apply schedules
        for zone_id, zone_data in self.ztl_coordinates.items():
            # Extract properties
            name = zone_data['properties']['name']
            boundaries = zone_data['polygon']

            # Create the zone
            zone_id_str = f'naples-ztl-{zone_id}'
            zone = Zone(id=zone_id_str, name=name, city=self.city, boundaries=boundaries)

            # Add restrictions if available
            if name in ztl_hours:
                for day_range, time_range in ztl_hours[name].items():
                    restrictions = self._parse_restriction(day_range, time_range)
                    for restriction in restrictions:
                        zone.add_restriction(restriction)

            zones.append(zone)

        return zones

    def _get_ztl_hours(self) -> dict[str, dict[str, str]]:
        """Get ZTL operating hours from HTML content.

        Returns:
            Dictionary with ZTL names as keys and schedules as values
        """
        hours: dict[str, dict[str, str]] = {}

        try:
            # Fetch HTML content
            html_content = self.get_html_content(self.ztl_page_path)

            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(html_content, 'html.parser')

            # Find ZTL info sections
            ztl_sections = soup.find_all('div', class_='ztl-info')

            for section in ztl_sections:
                # Extract zone name
                name_element = section.find('h3')
                if not name_element:
                    continue

                name = name_element.text.strip()

                # Extract operating hours
                hours_element = section.find('p')
                if not hours_element:
                    continue

                hours_text = hours_element.text.strip()

                # Process operating hours
                # Typically in format: "Orari: Dal lunedì al venerdì 07:00-19:00, Sabato e domenica 10:00-14:00"
                hours_text = hours_text.replace('Orari:', '').strip()

                # Initialize dict for this ZTL
                hours[name] = {}

                # Parse different time ranges
                for time_range in hours_text.split(','):
                    time_range = time_range.strip()

                    # Extract day and time information using regex
                    if 'lunedì al venerdì' in time_range.lower():
                        days = 'Monday-Friday'
                        time_match = re.search(r'(\d{2}:\d{2})-(\d{2}:\d{2})', time_range)
                        if time_match:
                            time_str = f'{time_match.group(1)}-{time_match.group(2)}'
                            hours[name][days] = time_str

                    elif 'sabato e domenica' in time_range.lower():
                        days = 'Saturday-Sunday'
                        time_match = re.search(r'(\d{2}:\d{2})-(\d{2}:\d{2})', time_range)
                        if time_match:
                            time_str = f'{time_match.group(1)}-{time_match.group(2)}'
                            hours[name][days] = time_str

                    # Add more patterns as needed for different day formats
                    else:
                        # Try to extract time range anyway
                        time_match = re.search(r'(\d{2}:\d{2})-(\d{2}:\d{2})', time_range)
                        if time_match:
                            time_str = f'{time_match.group(1)}-{time_match.group(2)}'
                            # If no specific days mentioned, assume Monday-Friday
                            hours[name]['Monday-Friday'] = time_str

            # If no hours found from HTML, use default schedule based on our knowledge
            if not hours:
                # Default schedules for known ZTLs
                default_hours = {
                    'ZTL Centro Antico': {'Monday-Friday': '07:00-19:00', 'Saturday-Sunday': '10:00-14:00'},
                    'ZTL Morelli - Filangieri - Mille': {'Monday-Friday': '08:00-18:00'},
                    'ZTL Tarsia - Pignasecca - Dante': {'Monday-Friday': '09:00-17:00'},
                    'ZTL Belledonne, Martiri, Poerio': {'Monday-Friday': '08:00-18:00'},
                    'ZTL Marechiaro': {'Saturday-Sunday': '08:00-19:00'},
                }
                hours = default_hours

        except Exception:
            # If there's an error, provide default schedules
            hours = {
                'ZTL Centro Antico': {'Monday-Friday': '07:00-19:00', 'Saturday-Sunday': '10:00-14:00'},
                'ZTL Morelli - Filangieri - Mille': {'Monday-Friday': '08:00-18:00'},
                'ZTL Tarsia - Pignasecca - Dante': {'Monday-Friday': '09:00-17:00'},
                'ZTL Belledonne, Martiri, Poerio': {'Monday-Friday': '08:00-18:00'},
                'ZTL Marechiaro': {'Saturday-Sunday': '08:00-19:00'},
            }

        return hours

    def _parse_restriction(self, day_range: str, time_range: str) -> list[Restriction]:
        """Parse restriction from day range and time range.

        Args:
            day_range: String with day range (e.g., "Monday-Friday")
            time_range: String with time range (e.g., "07:00-19:00")

        Returns:
            List of Restriction objects
        """
        restrictions = []

        # Parse day range
        days = self._expand_day_range(day_range)

        # Create restriction with the time range
        restriction = Restriction(days=days, start_time=time_range.split('-')[0], end_time=time_range.split('-')[1])
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
            except ValueError:
                # Default to weekdays if days not recognized
                return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

            # Return the range of days
            return day_order[start_index : end_index + 1]

        # Handle single day
        elif day_range in day_order:
            return [day_range]

        # Default to weekdays if format not recognized
        return ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
