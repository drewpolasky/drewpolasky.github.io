# GEFS Forecast Plume Diagram Generator

Python script for generating plume diagrams from ensemble weather forecast data using the Herbie package.

## Features

- Fetch ensemble forecast data from multiple models:
  - **GEFS** (Global Ensemble Forecast System)
  - **AIFS** (AI Forecast System) ✨
  - **AIGFS** (AI Global Forecast System) ✨
  - **ECMWF** (European Centre for Medium-Range Weather Forecasts)

- Support for multiple meteorological variables:
  - Temperature (2m)
  - Pressure (mean sea level)
  - Wind speed (10m)

- Generate professional plume diagrams showing:
  - Individual ensemble members
  - Percentile bands (10-90, 25-75)
  - Median forecast

## Installation

```bash
# Install dependencies
pip install -r requirements.txt
```

## Usage

### Basic Usage

Generate a GEFS temperature plume diagram:
```bash
python gefs_forecast.py --model GEFS --variable temperature
```

Generate an AIFS pressure plume diagram:
```bash
python gefs_forecast.py --model AIFS --variable pressure
```

Generate an AIGFS wind speed plume diagram:
```bash
python gefs_forecast.py --model AIGFS --variable wind
```

### Advanced Usage

Specify location (latitude/longitude):
```bash
python gefs_forecast.py --model AIFS --variable temperature --lat 40.0 --lon -105.0
```

Save to file:
```bash
python gefs_forecast.py --model AIGFS --variable temperature --output plume_aigfs.png
```

Use synthetic data (for testing without API access):
```bash
python gefs_forecast.py --model AIFS --variable temperature --synthetic
```

### Command-Line Options

- `--model`: Forecast model (`GEFS`, `AIFS`, `AIGFS`, `ECMWF`)
- `--variable`: Variable to plot (`temperature`, `pressure`, `wind`)
- `--lat`: Latitude for point forecast (default: 40.0)
- `--lon`: Longitude for point forecast (default: -105.0)
- `--output`: Output file path (default: display on screen)
- `--synthetic`: Use synthetic data instead of fetching real data

## Python API

```python
from gefs_forecast import PlumeDiagram

# Create plume diagram for AIFS temperature
plume = PlumeDiagram(model='AIFS', variable='temperature')

# Fetch data
plume.fetch_data(lat=40.0, lon=-105.0)

# Generate plot
plume.plot_plume(output_file='aifs_temperature_plume.png')
```

## Model Information

### GEFS (Global Ensemble Forecast System)
- 30 ensemble members
- NOAA operational ensemble system
- Color: Blue (#0066cc)

### AIFS (AI Forecast System)
- 50 ensemble members
- AI-based weather prediction system
- Color: Green (#00cc66)

### AIGFS (AI Global Forecast System)
- 50 ensemble members
- AI-based global forecast system
- Color: Orange (#cc6600)

### ECMWF
- 50 ensemble members
- European Centre operational ensemble
- Color: Red (#cc0000)

## Data Source

This script uses the [Herbie](https://herbie.readthedocs.io/) package to fetch weather forecast data from various sources. Herbie provides a unified interface to download and process GRIB2 files from multiple weather prediction models.

## Notes

- Data availability depends on the model and data provider
- Some models (AIFS, AIGFS) may require specific data access or API keys
- If real data is unavailable, use the `--synthetic` flag to generate example plume diagrams
- Default location is Boulder, Colorado (40.0°N, 105.0°W)

## Example Output

The script generates publication-quality plume diagrams showing:
- Ensemble spread as shaded regions
- Individual member traces (faint lines)
- Median forecast (bold line)
- Statistical percentiles (10-90, 25-75)

## Author

Drew Polasky  
NOAA Physical Sciences Lab / CIRES
