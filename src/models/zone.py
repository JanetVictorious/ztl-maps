"""Data model for environmental zones with boundaries and properties."""


class Zone:
    """Environmental zone with boundaries."""

    def __init__(self, id, name, city, boundaries, restrictions=None):  # pylint: disable=too-many-positional-arguments,redefined-builtin
        """Initialize the zone.

        Args:
            id: Unique identifier for the zone
            name: Name of the zone (e.g., "ZTL Centro Storico")
            city: City where the zone is located
            boundaries: List of [longitude, latitude] coordinates defining the zone boundary
            restrictions: Optional list of Restriction objects for this zone
        """
        self.id = id
        self.name = name
        self.city = city
        self.boundaries = boundaries
        self.restrictions = restrictions or []

    def is_active_at(self, datetime):
        """Check if restrictions are active at a given time.

        Args:
            datetime: A datetime object to check against restrictions

        Returns:
            bool: True if any restriction is active at the given time, False otherwise
        """
        if not self.restrictions:
            return False

        return any(restriction.is_active_at(datetime) for restriction in self.restrictions)

    def add_restriction(self, restriction):
        """Add a restriction to the zone.

        Args:
            restriction: A Restriction object to add to this zone
        """
        self.restrictions.append(restriction)

    def to_geojson(self):
        """Convert zone to GeoJSON format for mapping.

        Returns:
            dict: A GeoJSON Feature representing this zone
        """
        return {
            'type': 'Feature',
            'properties': {'id': self.id, 'name': self.name, 'city': self.city},
            'geometry': {'type': 'Polygon', 'coordinates': [self.boundaries]},
        }
