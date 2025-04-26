#!/usr/bin/env python3
"""Script to visualize ZTL zones for any city.

Usage: uv run -m src.scripts.visualize_ztl_zones [city_name] [output_file]
"""

import argparse
import importlib
from datetime import datetime
from pathlib import Path

import folium
from folium.features import DivIcon

from src.models.city import City
from src.open_street_map.map import create_map_for_city, save_map

# List of distinct colors for zones
ZONE_COLORS = [
    '#e6194B',
    '#3cb44b',
    '#ffe119',
    '#4363d8',
    '#f58231',
    '#911eb4',
    '#42d4f4',
    '#f032e6',
    '#bfef45',
    '#fabed4',
    '#469990',
    '#dcbeff',
    '#9A6324',
    '#fffac8',
    '#800000',
    '#aaffc3',
]


def get_scraper_class(city_name):
    """Dynamically import and return the scraper class for the given city."""
    try:
        # Convert city name to CamelCase and add 'Scraper' suffix
        city_pascal = ''.join(word.capitalize() for word in city_name.split('_'))
        class_name = f'{city_pascal}Scraper'

        # Import the module
        module = importlib.import_module(f'src.scrapers.city_specific.{city_name.lower()}')

        # Get the scraper class
        scraper_class = getattr(module, class_name)
        return scraper_class
    except (ImportError, AttributeError) as e:
        available_scrapers = get_available_scrapers()
        raise ValueError(
            f"No scraper found for city '{city_name}'. Available scrapers: {', '.join(available_scrapers)}"
        ) from e


def get_available_scrapers():
    """Return a list of available city scrapers."""
    scrapers = []
    scraper_path = Path(__file__).parent.parent / 'scrapers' / 'city_specific'

    for file in scraper_path.glob('*.py'):
        if file.name != '__init__.py' and file.stem not in ['florence_ztl_coordinates']:
            scrapers.append(file.stem)

    return scrapers


def create_tooltip_content(zone):
    """Create enhanced tooltip content with active times."""
    content = f'<b>{zone.name}</b><br>'

    if zone.restrictions:
        content += '<b>Active Times:</b><br>'
        for restriction in zone.restrictions:
            days = ', '.join(restriction.days)
            content += f'{days}: {restriction.start_time} - {restriction.end_time}<br>'
    else:
        content += 'No time restrictions'

    # Check if currently active
    current_time = datetime.now()
    is_active = zone.is_active_at(current_time)
    status = 'ACTIVE' if is_active else 'Inactive'
    content += f'<br><b>Current Status:</b> {status}'

    return content


def create_city_visualization(city_name, output_file=None):  # pylint: disable=too-many-locals
    """Create a visualization for the specified city's ZTL zones."""
    # Get the scraper class and instantiate it
    scraper_class = get_scraper_class(city_name)
    scraper = scraper_class()

    # Get zones from the scraper
    zones = scraper.parse_zones()

    # Create a City object with the zones
    city = City(name=scraper.city, zones=zones)

    # Create a map for the city
    city_map = create_map_for_city(city)

    # Add custom layer with enhanced tooltips
    city_layer = folium.FeatureGroup(name=f'{city.name} ZTL Zones')

    # Create a style function that uses different colors for different zones
    def get_unique_zone_color(zone_index, is_active):
        """Get a unique color for each zone."""
        color = ZONE_COLORS[zone_index % len(ZONE_COLORS)]
        # Adjust color intensity if active
        return color if is_active else color

    # Add responsive label script to the map
    responsive_label_js = """
    <script>
    document.addEventListener('DOMContentLoaded', function() {
        // Get all zone labels
        var zoneLabels = document.querySelectorAll('.zone-label');

        // Function to update label sizes based on zoom
        function updateLabelSizes() {
            var zoom = map.getZoom();
            var baseFontSize = Math.max(8, Math.min(16, zoom * 1.2));

            zoneLabels.forEach(function(label) {
                label.style.fontSize = baseFontSize + 'pt';
            });
        }

        // Update labels on zoom
        map.on('zoomend', updateLabelSizes);

        // Initial update
        setTimeout(updateLabelSizes, 100);
    });
    </script>
    """
    city_map.map.get_root().html.add_child(folium.Element(responsive_label_js))

    # Add zones to the map
    for i, zone in enumerate(city.zones):
        # Determine if zone is active now
        current_time = datetime.now()
        is_active = zone.is_active_at(current_time)

        # Get color for this zone
        color = get_unique_zone_color(i, is_active)

        # Higher transparency for all zones
        opacity = 0.45 if is_active else 0.3

        # Create GeoJSON with enhanced tooltip
        tooltip = folium.Tooltip(create_tooltip_content(zone))

        geojson = folium.GeoJson(
            zone.to_geojson(),
            name=zone.name,
            style_function=lambda x, color=color, opacity=opacity: {
                'fillColor': color,
                'color': '#000000',
                'fillOpacity': opacity,
                'weight': 1.5,
            },
        )

        # Add the tooltip to the GeoJSON
        geojson.add_child(tooltip)

        # Add a label in the center of the zone with responsive sizing
        if len(zone.boundaries) > 0:
            # Calculate center of zone
            lat_sum = sum(coord[1] for coord in zone.boundaries)
            lon_sum = sum(coord[0] for coord in zone.boundaries)
            center = [lat_sum / len(zone.boundaries), lon_sum / len(zone.boundaries)]

            # Add a label with a unique class for responsive sizing
            folium.map.Marker(
                location=center,
                icon=DivIcon(
                    icon_size=(150, 36),
                    icon_anchor=(75, 18),
                    html=f'<div class="zone-label" style="font-weight: bold; color: black; text-shadow: 1px 1px 1px white, -1px -1px 1px white, 1px -1px 1px white, -1px 1px 1px white;">{zone.name}</div>',  # noqa: E501
                ),
            ).add_to(city_layer)

        # Add the GeoJSON to the city layer
        geojson.add_to(city_layer)

    # Add the city layer to the map
    city_layer.add_to(city_map.map)

    # Add layer control
    folium.LayerControl().add_to(city_map.map)

    # Save the map to a file if specified
    if output_file:
        output_path = save_map(city_map, output_file)
        print(f'Map saved to {output_path}')

    return city_map


def main():
    """Main function to parse arguments and create visualization."""
    parser = argparse.ArgumentParser(description='Visualize ZTL zones for a city')
    parser.add_argument('city', help='City name (e.g., florence, milan)')
    parser.add_argument('--output', '-o', help='Output HTML file path')

    args = parser.parse_args()

    try:
        # Create output file path if not specified
        if not args.output:
            output_dir = Path('visualizations')
            output_dir.mkdir(exist_ok=True)
            args.output = output_dir / f'{args.city}_ztl_zones.html'

        # Create the visualization
        create_city_visualization(args.city, args.output)

    except ValueError as e:
        print(f'Error: {e}')
        return 1

    return 0


if __name__ == '__main__':
    exit(main())
