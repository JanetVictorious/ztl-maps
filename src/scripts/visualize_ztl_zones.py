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
from src.models.restriction import Restriction
from src.models.zone import Zone
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


def is_currently_active(zone, current_time=None):
    """Check if a zone is currently active, with special handling for overnight restrictions.

    Args:
        zone: The Zone object to check
        current_time: Optional datetime object (defaults to now)

    Returns:
        bool: True if the zone is active, False otherwise
    """
    if current_time is None:
        current_time = datetime.now()

    # For debugging
    day_name = current_time.strftime('%A')
    current_hour = current_time.hour
    current_minute = current_time.minute

    # Get zone name for debugging
    zone_name = zone.name
    is_night_zone = '(Night)' in zone_name

    # Log current time for debugging
    print(f'Checking zone {zone_name} at {day_name} {current_hour}:{current_minute:02d}')

    for restriction in zone.restrictions:
        # Log restriction for debugging
        days_str = ', '.join(restriction.days)
        print(f'  Restriction: {days_str} from {restriction.start_time} to {restriction.end_time}')

        # Standard check using zone's is_active_at method
        if zone.is_active_at(current_time):
            print('  ✓ Standard check: Active')
            return True

        # Special handling for nighttime zones with time range crossing midnight
        if (
            is_night_zone
            and 'Thursday' in restriction.days
            and 'Friday' in restriction.days
            and 'Saturday' in restriction.days
        ):
            start_hour = restriction.start_time.hour
            end_hour = restriction.end_time.hour

            # Direct check for Florence nighttime zones (Thursday-Saturday, 23:00-03:00)
            if start_hour == 23 and end_hour == 3:
                # Check if today is one of the active days and if current time is after start time
                if day_name in restriction.days and current_hour >= start_hour:
                    print('  ✓ Nighttime zone active (same day after start)')
                    return True

                # Check if it's early morning after an active night
                # Get previous day
                days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                prev_day_idx = (days.index(day_name) - 1) % 7
                prev_day = days[prev_day_idx]

                # If previous day is in restriction days and current time is before end time
                if prev_day in restriction.days and current_hour < end_hour:
                    print('  ✓ Nighttime zone active (next day before end)')
                    return True

    print('  ✗ Zone inactive')
    return False


def create_tooltip_content(zone, zone_type='daytime'):
    """Create enhanced tooltip content with active times.

    Args:
        zone: The ZTL zone object
        zone_type: Type of zone (daytime or nighttime)

    Returns:
        str: HTML content for the tooltip
    """
    content = f'<b>{zone.name}</b><br>'
    content += f'<b>Type:</b> {zone_type.capitalize()}<br>'

    if zone.restrictions:
        content += '<b>Active Times:</b><br>'
        for restriction in zone.restrictions:
            days = ', '.join(restriction.days)
            content += f'{days}: {restriction.start_time} - {restriction.end_time}<br>'
    else:
        content += 'No time restrictions'

    # Check if currently active using our custom function
    current_time = datetime.now()
    is_active = is_currently_active(zone, current_time)
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

    # Add toggle control between daytime and nighttime zones
    toggle_js = """
    <script>
    // Global variable to track which mode is active (daytime or nighttime)
    var activeMode = 'daytime';

    function toggleZoneModes() {
        // Toggle between daytime and nighttime
        if (activeMode === 'daytime') {
            activeMode = 'nighttime';
            document.getElementById('toggleButton').innerHTML = 'Show Daytime Zones';

            // Hide daytime layers
            document.querySelectorAll('.daytime-layer').forEach(function(element) {
                element.style.display = 'none';
            });

            // Show nighttime layers
            document.querySelectorAll('.nighttime-layer').forEach(function(element) {
                element.style.display = '';
            });
        } else {
            activeMode = 'daytime';
            document.getElementById('toggleButton').innerHTML = 'Show Nighttime Zones';

            // Hide nighttime layers
            document.querySelectorAll('.nighttime-layer').forEach(function(element) {
                element.style.display = 'none';
            });

            // Show daytime layers
            document.querySelectorAll('.daytime-layer').forEach(function(element) {
                element.style.display = '';
            });
        }
    }

    // Add button after map is loaded
    document.addEventListener('DOMContentLoaded', function() {
        var mapDiv = document.querySelector('.folium-map');

        // Create the toggle button
        var toggleButton = document.createElement('button');
        toggleButton.id = 'toggleButton';
        toggleButton.innerHTML = 'Show Nighttime Zones';
        toggleButton.onclick = toggleZoneModes;
        toggleButton.style.cssText = 'position:absolute; top:10px; right:10px; z-index:999; padding:8px 12px; background-color:#fff; border:2px solid #ccc; border-radius:4px; font-weight:bold; cursor:pointer;';

        // Add hover effect
        toggleButton.onmouseover = function() { this.style.backgroundColor = '#eee'; };
        toggleButton.onmouseout = function() { this.style.backgroundColor = '#fff'; };

        // Add button to map container
        mapDiv.appendChild(toggleButton);

        // Initially hide nighttime layers
        document.querySelectorAll('.nighttime-layer').forEach(function(element) {
            element.style.display = 'none';
        });
    });
    </script>
    """
    city_map.map.get_root().html.add_child(folium.Element(toggle_js))

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

    # Create daytime and nighttime feature groups
    daytime_layer = folium.FeatureGroup(name=f'{city.name} Daytime ZTL Zones')
    nighttime_layer = folium.FeatureGroup(name=f'{city.name} Nighttime ZTL Zones')

    # Add custom CSS class to layers for toggling
    daytime_js = f"""
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        var daytimeLayer = document.querySelector('[data-name="{city.name} Daytime ZTL Zones"]');
        if (daytimeLayer) {{
            daytimeLayer.classList.add('daytime-layer');
        }}
    }});
    </script>
    """

    nighttime_js = f"""
    <script>
    document.addEventListener('DOMContentLoaded', function() {{
        var nighttimeLayer = document.querySelector('[data-name="{city.name} Nighttime ZTL Zones"]');
        if (nighttimeLayer) {{
            nighttimeLayer.classList.add('nighttime-layer');
        }}
    }});
    </script>
    """

    city_map.map.get_root().html.add_child(folium.Element(daytime_js))
    city_map.map.get_root().html.add_child(folium.Element(nighttime_js))

    # Get all nighttime zones if available (Florence specific)
    night_zones = []
    if hasattr(scraper, 'ztl_coordinates'):
        night_zone_ids = [key for key in scraper.ztl_coordinates if key.startswith('night_')]
        for night_id in night_zone_ids:
            # Create a Zone object for each nighttime zone
            sector_name = night_id.replace('night_', '')
            night_zone = Zone(
                id=f'night-{city_name.lower()}-settore-{sector_name.lower()}',
                name=f'ZTL Settore {sector_name} (Night)',
                city=city.name,
                boundaries=scraper._get_approximate_coordinates_for_sector(sector_name),
            )

            # Add nighttime restrictions
            # For Florence, nights are Thursday-Saturday, 23:00-3:00
            night_restriction = Restriction(
                days=['Thursday', 'Friday', 'Saturday'], start_time='23:00', end_time='3:00'
            )
            night_zone.add_restriction(night_restriction)
            night_zones.append(night_zone)

    # Create a style function that uses different colors for different zones
    def get_unique_zone_color(zone_index, is_active):
        """Get a unique color for each zone."""
        color = ZONE_COLORS[zone_index % len(ZONE_COLORS)]
        # Adjust color intensity if active
        return color if is_active else color

    # Add daytime zones to the map
    for i, zone in enumerate(city.zones):
        # Determine if zone is active now using our custom function
        current_time = datetime.now()
        is_active = is_currently_active(zone, current_time)

        # Get color for this zone
        color = get_unique_zone_color(i, is_active)

        # Higher transparency for all zones
        opacity = 0.45 if is_active else 0.3

        # Create GeoJSON with enhanced tooltip
        tooltip = folium.Tooltip(create_tooltip_content(zone, 'daytime'))

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
            ).add_to(daytime_layer)

        # Add the GeoJSON to the city layer
        geojson.add_to(daytime_layer)

    # Add nighttime zones to the map
    for i, zone in enumerate(night_zones):
        # Determine if zone is active now using our custom function
        current_time = datetime.now()
        is_active = is_currently_active(zone, current_time)

        # Get color for this zone (use a different color scheme for nighttime)
        color = get_unique_zone_color(i + len(city.zones), is_active)  # Offset to get different colors

        # Higher transparency for all zones
        opacity = 0.45 if is_active else 0.3

        # Create GeoJSON with enhanced tooltip
        tooltip = folium.Tooltip(create_tooltip_content(zone, 'nighttime'))

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
            ).add_to(nighttime_layer)

        # Add the GeoJSON to the nighttime layer
        geojson.add_to(nighttime_layer)

    # Add the layers to the map
    daytime_layer.add_to(city_map.map)
    nighttime_layer.add_to(city_map.map)

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
