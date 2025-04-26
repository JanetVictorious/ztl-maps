"""Model representing a city with its collection of zones."""


class City:
    """City with environmental zones."""

    def __init__(self, name, country='Italy', zones=None):
        """Initialize a city.

        Args:
            name: Name of the city
            country: Country where the city is located (default: Italy)
            zones: Optional list of Zone objects within this city
        """
        self.name = name
        self.country = country
        self.zones = zones or []

    def add_zone(self, zone):
        """Add a zone to the city.

        Args:
            zone: A Zone object to add to this city
        """
        self.zones.append(zone)

    def get_zone_by_id(self, zone_id):
        """Get a zone by its ID.

        Args:
            zone_id: ID of the zone to retrieve

        Returns:
            Zone: The requested zone or None if not found
        """
        for zone in self.zones:
            if zone.id == zone_id:
                return zone
        return None

    def to_geojson(self):
        """Convert all city zones to GeoJSON format.

        Returns:
            dict: A GeoJSON FeatureCollection containing all zones
        """
        return {
            'type': 'FeatureCollection',
            'features': [zone.to_geojson() for zone in self.zones],
            'properties': {'name': self.name, 'country': self.country, 'zone_count': len(self.zones)},
        }
