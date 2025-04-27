# ZTL Maps

A Python application for tracking and visualizing Limited Traffic Zones (ZTL) in Italian cities.

## Features

- **City & Zone Management**: Store and retrieve information about cities and their traffic restriction zones
- **Time-based Restrictions**: Check if zones are active based on day and time
- **Interactive Maps**: Visualize zones on interactive maps with Folium/OpenStreetMap
- **REST API**: Access data programmatically via RESTful endpoints
- **Scraping Tools**: Collect zone data from official city websites

## Usage

### API Endpoints

```bash
# Get all available cities
GET /cities

# Get details for a specific city
GET /cities/{city_name}

# Get currently active zones for a city
GET /cities/{city_name}/active-zones
```

### Map Visualization

```python
from src.models.city import City
from src.open_street_map.visualizer import ZoneVisualizer

# Load city data
city = load_city("Milano")

# Create visualizer and highlight active zones
visualizer = ZoneVisualizer()
map_with_active_zones = visualizer.visualize_active_zones(city)

# Save the map
map_with_active_zones.map.save("milano_active_zones.html")
```

## Data Attribution

The ZTL coordinate data for Italian cities is sourced from their respective municipal websites under the CC BY 4.0 license:

- **Florence**: Data provided by the City of Florence. Licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- **Bologna**: Data provided by the City of Bologna. Licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)

This project uses this data with modifications for visualization purposes.

## Development

```bash
# Install uv
pip install uv

# Install dependencies
make sync-venv

# Run tests
make run-tests

# Check test coverage
make run-tests-cov
```
