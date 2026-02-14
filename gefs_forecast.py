#!/usr/bin/env python3
"""
GEFS Forecast Plume Diagram Generator

This script uses the Herbie package to fetch ensemble forecast data from various
numerical weather prediction models (GEFS, AIFS, AIGFS) and generates plume diagrams
showing forecast uncertainty.

Dependencies:
    - herbie-data
    - matplotlib
    - numpy
    - pandas
    - xarray

Author: Drew Polasky
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional, Union

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

try:
    from herbie import Herbie, FastHerbie
    HERBIE_AVAILABLE = True
except ImportError:
    HERBIE_AVAILABLE = False
    Herbie = None
    FastHerbie = None


class PlumeDiagram:
    """Class for generating plume diagrams from ensemble forecast data."""
    
    # Model configurations
    MODELS = {
        'GEFS': {
            'name': 'GEFS',
            'full_name': 'Global Ensemble Forecast System',
            'source': 'gefs',
            'color': '#0066cc',
            'members': 30,  # GEFS has 30 ensemble members
        },
        'AIFS': {
            'name': 'AIFS',
            'full_name': 'AI Forecast System',
            'source': 'aifs',
            'color': '#00cc66',
            'members': 50,  # AIFS ensemble members
        },
        'AIGFS': {
            'name': 'AIGFS',
            'full_name': 'AI Global Forecast System',
            'source': 'aigfs',
            'color': '#cc6600',
            'members': 50,  # AIGFS ensemble members
        },
        'ECMWF': {
            'name': 'ECMWF',
            'full_name': 'European Centre for Medium-Range Weather Forecasts',
            'source': 'ecmwf',
            'color': '#cc0000',
            'members': 50,
        }
    }
    
    # Variable configurations
    VARIABLES = {
        'temperature': {
            'grib_name': 'TMP:2 m above ground',
            'short_name': 't2m',
            'units': '°C',
            'convert': lambda x: x - 273.15,  # Kelvin to Celsius
            'ylabel': 'Temperature (°C)',
        },
        'pressure': {
            'grib_name': 'PRMSL:mean sea level',
            'short_name': 'msl',
            'units': 'hPa',
            'convert': lambda x: x / 100,  # Pa to hPa
            'ylabel': 'Pressure (hPa)',
        },
        'wind': {
            'grib_name': 'WIND:10 m above ground',
            'short_name': 'si10',
            'units': 'm/s',
            'convert': lambda x: x,
            'ylabel': 'Wind Speed (m/s)',
        }
    }
    
    def __init__(self, model: str, variable: str = 'temperature'):
        """
        Initialize PlumeDiagram object.
        
        Args:
            model: Model name ('GEFS', 'AIFS', 'AIGFS', or 'ECMWF')
            variable: Variable to plot ('temperature', 'pressure', or 'wind')
        """
        if model not in self.MODELS:
            raise ValueError(f"Model must be one of {list(self.MODELS.keys())}")
        if variable not in self.VARIABLES:
            raise ValueError(f"Variable must be one of {list(self.VARIABLES.keys())}")
        
        self.model = model
        self.variable = variable
        self.model_config = self.MODELS[model]
        self.var_config = self.VARIABLES[variable]
        self.data = None
        
    def fetch_data(self, 
                   init_time: Optional[datetime] = None,
                   lat: float = 40.0,
                   lon: float = -105.0,
                   fxx: List[int] = None) -> pd.DataFrame:
        """
        Fetch ensemble forecast data using Herbie.
        
        Args:
            init_time: Initialization time for the forecast (default: latest)
            lat: Latitude for point forecast
            lon: Longitude for point forecast
            fxx: List of forecast hours (default: 0 to 120 by 6)
            
        Returns:
            DataFrame with ensemble forecast data
        """
        if init_time is None:
            init_time = datetime.utcnow() - timedelta(hours=6)
        
        if fxx is None:
            fxx = list(range(0, 121, 6))  # 0 to 120 hours by 6-hour intervals
        
        print(f"Fetching {self.model_config['name']} data for {init_time.strftime('%Y-%m-%d %H:%M UTC')}")
        print(f"Variable: {self.variable}, Location: ({lat:.2f}°N, {lon:.2f}°E)")
        
        # Check if Herbie is available
        if not HERBIE_AVAILABLE:
            print("Warning: Herbie package not installed. Using synthetic data.")
            print("Install with: pip install herbie-data")
            return self._generate_synthetic_data(fxx)
        
        ensemble_data = []
        
        try:
            # For GEFS, we can use FastHerbie for efficient ensemble retrieval
            if self.model == 'GEFS':
                ensemble_data = self._fetch_gefs(init_time, lat, lon, fxx)
            elif self.model == 'AIFS':
                ensemble_data = self._fetch_aifs(init_time, lat, lon, fxx)
            elif self.model == 'AIGFS':
                ensemble_data = self._fetch_aigfs(init_time, lat, lon, fxx)
            elif self.model == 'ECMWF':
                ensemble_data = self._fetch_ecmwf(init_time, lat, lon, fxx)
            
            # Convert to DataFrame
            self.data = pd.DataFrame(ensemble_data)
            return self.data
            
        except Exception as e:
            print(f"Error fetching data: {e}")
            print("Generating synthetic data for demonstration purposes...")
            return self._generate_synthetic_data(fxx)
    
    def _fetch_gefs(self, init_time: datetime, lat: float, lon: float, fxx: List[int]) -> List[dict]:
        """Fetch GEFS ensemble data using Herbie."""
        ensemble_data = []
        
        for member in range(self.model_config['members']):
            member_data = []
            
            for f in fxx:
                try:
                    # Create Herbie object for GEFS member
                    H = Herbie(
                        init_time,
                        model='gefs',
                        product='atmos',
                        member=member,
                        fxx=f
                    )
                    
                    # Get the data (this is a simplified approach)
                    # In practice, you'd use H.xarray() to get the full dataset
                    # and extract the point value
                    ds = H.xarray(self.var_config['grib_name'])
                    
                    # Extract point value (nearest neighbor)
                    value = ds.sel(latitude=lat, longitude=lon, method='nearest')
                    value = self.var_config['convert'](float(value.values))
                    
                    member_data.append({
                        'member': member,
                        'forecast_hour': f,
                        'value': value
                    })
                    
                except Exception as e:
                    print(f"Warning: Could not fetch GEFS member {member}, hour {f}: {e}")
                    continue
            
            ensemble_data.extend(member_data)
        
        return ensemble_data
    
    def _fetch_aifs(self, init_time: datetime, lat: float, lon: float, fxx: List[int]) -> List[dict]:
        """Fetch AIFS (AI Forecast System) data using Herbie."""
        ensemble_data = []
        
        # AIFS is newer and may have different data structure
        # This is a placeholder implementation
        for member in range(self.model_config['members']):
            member_data = []
            
            for f in fxx:
                try:
                    # AIFS data might be available through different sources
                    # This is a conceptual implementation
                    H = Herbie(
                        init_time,
                        model='aifs',
                        product='ens',
                        member=member,
                        fxx=f
                    )
                    
                    # Get the data
                    ds = H.xarray(self.var_config['short_name'])
                    
                    # Extract point value
                    value = ds.sel(latitude=lat, longitude=lon, method='nearest')
                    value = self.var_config['convert'](float(value.values))
                    
                    member_data.append({
                        'member': member,
                        'forecast_hour': f,
                        'value': value
                    })
                    
                except Exception as e:
                    print(f"Warning: Could not fetch AIFS member {member}, hour {f}: {e}")
                    continue
            
            ensemble_data.extend(member_data)
        
        return ensemble_data
    
    def _fetch_aigfs(self, init_time: datetime, lat: float, lon: float, fxx: List[int]) -> List[dict]:
        """Fetch AIGFS (AI Global Forecast System) data using Herbie."""
        ensemble_data = []
        
        # AIGFS implementation
        for member in range(self.model_config['members']):
            member_data = []
            
            for f in fxx:
                try:
                    # AIGFS data access
                    H = Herbie(
                        init_time,
                        model='aigfs',
                        product='ens',
                        member=member,
                        fxx=f
                    )
                    
                    # Get the data
                    ds = H.xarray(self.var_config['short_name'])
                    
                    # Extract point value
                    value = ds.sel(latitude=lat, longitude=lon, method='nearest')
                    value = self.var_config['convert'](float(value.values))
                    
                    member_data.append({
                        'member': member,
                        'forecast_hour': f,
                        'value': value
                    })
                    
                except Exception as e:
                    print(f"Warning: Could not fetch AIGFS member {member}, hour {f}: {e}")
                    continue
            
            ensemble_data.extend(member_data)
        
        return ensemble_data
    
    def _fetch_ecmwf(self, init_time: datetime, lat: float, lon: float, fxx: List[int]) -> List[dict]:
        """Fetch ECMWF ensemble data using Herbie."""
        ensemble_data = []
        
        for member in range(self.model_config['members']):
            member_data = []
            
            for f in fxx:
                try:
                    H = Herbie(
                        init_time,
                        model='ecmwf',
                        product='ens',
                        member=member,
                        fxx=f
                    )
                    
                    ds = H.xarray(self.var_config['short_name'])
                    value = ds.sel(latitude=lat, longitude=lon, method='nearest')
                    value = self.var_config['convert'](float(value.values))
                    
                    member_data.append({
                        'member': member,
                        'forecast_hour': f,
                        'value': value
                    })
                    
                except Exception as e:
                    print(f"Warning: Could not fetch ECMWF member {member}, hour {f}: {e}")
                    continue
            
            ensemble_data.extend(member_data)
        
        return ensemble_data
    
    def _generate_synthetic_data(self, fxx: List[int]) -> pd.DataFrame:
        """Generate synthetic ensemble data for demonstration."""
        print("Generating synthetic data...")
        
        # Base value depends on variable
        if self.variable == 'temperature':
            base_value = 15.0
            trend_amp = 5.0
            noise_amp = 8.0
        elif self.variable == 'pressure':
            base_value = 1013.0
            trend_amp = 10.0
            noise_amp = 15.0
        else:  # wind
            base_value = 10.0
            trend_amp = 2.0
            noise_amp = 4.0
        
        # AIFS and AIGFS have slightly tighter spread
        spread_factor = 0.8 if self.model in ['AIFS', 'AIGFS'] else 1.0
        
        data = []
        for member in range(self.model_config['members']):
            for f in fxx:
                trend = np.sin(f / 20) * trend_amp
                noise = (np.random.random() - 0.5) * noise_amp * spread_factor
                value = base_value + trend + noise
                
                data.append({
                    'member': member,
                    'forecast_hour': f,
                    'value': value
                })
        
        return pd.DataFrame(data)
    
    def calculate_percentiles(self, hours: Optional[List[int]] = None) -> pd.DataFrame:
        """
        Calculate percentiles from ensemble data.
        
        Args:
            hours: Forecast hours to calculate percentiles for
            
        Returns:
            DataFrame with percentile statistics
        """
        if self.data is None:
            raise ValueError("No data available. Call fetch_data() first.")
        
        if hours is None:
            hours = sorted(self.data['forecast_hour'].unique())
        
        percentiles = []
        
        for hour in hours:
            hour_data = self.data[self.data['forecast_hour'] == hour]['value']
            
            if len(hour_data) > 0:
                percentiles.append({
                    'forecast_hour': hour,
                    'p10': hour_data.quantile(0.10),
                    'p25': hour_data.quantile(0.25),
                    'p50': hour_data.quantile(0.50),
                    'p75': hour_data.quantile(0.75),
                    'p90': hour_data.quantile(0.90),
                    'mean': hour_data.mean(),
                    'min': hour_data.min(),
                    'max': hour_data.max(),
                })
        
        return pd.DataFrame(percentiles)
    
    def plot_plume(self, output_file: Optional[str] = None, title: Optional[str] = None):
        """
        Generate and save plume diagram.
        
        Args:
            output_file: Path to save the figure (default: None, displays instead)
            title: Custom title for the plot
        """
        if self.data is None:
            raise ValueError("No data available. Call fetch_data() first.")
        
        # Calculate percentiles
        stats = self.calculate_percentiles()
        
        # Create figure
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # Plot individual ensemble members with low alpha
        for member in self.data['member'].unique():
            member_data = self.data[self.data['member'] == member]
            ax.plot(
                member_data['forecast_hour'],
                member_data['value'],
                color=self.model_config['color'],
                alpha=0.1,
                linewidth=0.5
            )
        
        # Plot percentile bands
        ax.fill_between(
            stats['forecast_hour'],
            stats['p10'],
            stats['p90'],
            color=self.model_config['color'],
            alpha=0.2,
            label='10-90 percentile'
        )
        
        ax.fill_between(
            stats['forecast_hour'],
            stats['p25'],
            stats['p75'],
            color=self.model_config['color'],
            alpha=0.3,
            label='25-75 percentile'
        )
        
        # Plot median
        ax.plot(
            stats['forecast_hour'],
            stats['p50'],
            color=self.model_config['color'],
            linewidth=2,
            label='Median',
            zorder=10
        )
        
        # Formatting
        ax.set_xlabel('Forecast Hour', fontsize=12)
        ax.set_ylabel(self.var_config['ylabel'], fontsize=12)
        
        if title is None:
            title = f"{self.model_config['full_name']} Plume Diagram\n{self.variable.capitalize()}"
        ax.set_title(title, fontsize=14, fontweight='bold')
        
        ax.legend(loc='best', fontsize=10)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        if output_file:
            plt.savefig(output_file, dpi=150, bbox_inches='tight')
            print(f"Plume diagram saved to {output_file}")
        else:
            plt.show()
        
        return fig, ax


def main():
    """Command-line interface for generating plume diagrams."""
    parser = argparse.ArgumentParser(
        description='Generate plume diagrams from ensemble forecast data'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        choices=['GEFS', 'AIFS', 'AIGFS', 'ECMWF'],
        default='GEFS',
        help='Forecast model to use'
    )
    
    parser.add_argument(
        '--variable',
        type=str,
        choices=['temperature', 'pressure', 'wind'],
        default='temperature',
        help='Variable to plot'
    )
    
    parser.add_argument(
        '--lat',
        type=float,
        default=40.0,
        help='Latitude for point forecast (default: 40.0)'
    )
    
    parser.add_argument(
        '--lon',
        type=float,
        default=-105.0,
        help='Longitude for point forecast (default: -105.0)'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Output file path (default: display on screen)'
    )
    
    parser.add_argument(
        '--synthetic',
        action='store_true',
        help='Use synthetic data instead of fetching real data'
    )
    
    args = parser.parse_args()
    
    # Create plume diagram object
    plume = PlumeDiagram(args.model, args.variable)
    
    # Fetch data
    if args.synthetic:
        plume.data = plume._generate_synthetic_data(list(range(0, 121, 6)))
    else:
        plume.fetch_data(lat=args.lat, lon=args.lon)
    
    # Generate plot
    plume.plot_plume(output_file=args.output)


if __name__ == '__main__':
    main()
