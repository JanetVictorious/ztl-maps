"""Scraper for Florence ZTL zones."""

import re

from bs4 import BeautifulSoup

from src.models.restriction import Restriction
from src.models.zone import Zone
from src.scrapers.base_scraper import BaseScraper


class FlorenceScraper(BaseScraper):
    """Scraper for Florence ZTL zones (Centro Storico, Settore A, etc.)."""

    def __init__(self):
        """Initialize the Florence scraper with the appropriate URL."""
        super().__init__(base_url='https://www.comune.fi.it')
        self.city = 'Firenze'
        self.ztl_page_path = '/mobility/ztl'  # Example path, would need adjustment for real implementation

    def parse_zones(self) -> list[Zone]:
        """Parse the HTML content and extract zone information.

        Returns:
            list: List of Zone objects representing Florence's ZTL zones
        """
        # Fetch HTML content
        html_content = self.get_html_content(self.ztl_page_path)

        # Parse HTML with BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')

        # Find all ZTL info sections
        ztl_info_sections = soup.find_all('div', class_='ztl-info')

        zones = []
        for section in ztl_info_sections:
            # Extract zone name
            name = section.find('h2').text.strip()

            # Generate zone ID
            zone_id = f'firenze-{name.lower().replace(" ", "-")}'

            # Extract operating hours text
            hours_text = section.find('p').text.strip()
            hours_text = hours_text.replace('Operating Hours:', '').strip()

            # Extract coordinates
            map_data = section.find('div', class_='map-data')
            coordinates_str = map_data['data-coordinates']
            boundaries = self._parse_coordinates(coordinates_str)

            # Create zone object
            zone = Zone(id=zone_id, name=name, city=self.city, boundaries=boundaries)

            # Parse and add restrictions
            restrictions = self._parse_restrictions(hours_text)
            for restriction in restrictions:
                zone.add_restriction(restriction)

            zones.append(zone)

        return zones

    def _parse_coordinates(self, coordinates_str: str) -> list[list[float]]:
        """Parse coordinate string into a list of [longitude, latitude] pairs.

        Args:
            coordinates_str: String containing coordinates in format "lon1,lat1;lon2,lat2;..."

        Returns:
            list: List of [longitude, latitude] pairs
        """
        coordinates = []
        pairs = coordinates_str.split(';')

        for pair in pairs:
            lon, lat = pair.split(',')
            coordinates.append([float(lon), float(lat)])

        return coordinates

    def _parse_restrictions(self, hours_text: str) -> list[Restriction]:  # pylint: disable=too-many-locals
        """Parse operating hours text and create restriction objects.

        Args:
            hours_text: Text containing operating hours information

        Returns:
            list: List of Restriction objects
        """
        restrictions = []

        # Split by comma for multiple time ranges
        time_ranges = hours_text.split(',')

        for time_range in time_ranges:
            time_range = time_range.strip()

            # Example pattern: "Monday-Friday 7:30-20:00"
            match = re.match(r'([A-Za-z]+)-([A-Za-z]+) (\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})', time_range)
            if not match:
                # Try single day pattern: "Saturday 10:00-16:00"
                match = re.match(r'([A-Za-z]+) (\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})', time_range)
                if match:
                    # Single day
                    day = match.group(1)
                    start_hour = match.group(2)
                    start_min = match.group(3)
                    end_hour = match.group(4)
                    end_min = match.group(5)

                    days = [day]
                    start_time = f'{start_hour}:{start_min}'
                    end_time = f'{end_hour}:{end_min}'

                    restrictions.append(Restriction(days=days, start_time=start_time, end_time=end_time))
                continue

            # Day range pattern matched
            start_day = match.group(1)
            end_day = match.group(2)
            start_hour = match.group(3)
            start_min = match.group(4)
            end_hour = match.group(5)
            end_min = match.group(6)

            # Generate list of days
            days = self._expand_day_range(start_day, end_day)
            start_time = f'{start_hour}:{start_min}'
            end_time = f'{end_hour}:{end_min}'

            restrictions.append(Restriction(days=days, start_time=start_time, end_time=end_time))

        return restrictions

    def _expand_day_range(self, start_day: str, end_day: str) -> list[str]:
        """Expand a day range like 'Monday-Friday' into a list of individual days.

        Args:
            start_day: Starting day of the range
            end_day: Ending day of the range

        Returns:
            list: List of days in the range
        """
        day_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

        start_index = day_order.index(start_day)
        end_index = day_order.index(end_day)

        return day_order[start_index : end_index + 1]
