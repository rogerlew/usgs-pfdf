# NOAA Data Module

This module provides functions to download precipitation frequency estimates and other datasets from the National Oceanic and Atmospheric Administration (NOAA).

## Overview

The `pfdf.data.noaa` package currently provides access to:

- **NOAA Atlas 14**: Precipitation frequency estimates for the United States

Additional NOAA datasets may be added in future releases.

## NOAA Atlas 14

NOAA Atlas 14 provides precipitation frequency estimates based on partial-duration and annual maximum series. These estimates are critical for hydrologic design, risk assessment, and hazard modeling applications.

### Coverage

Atlas 14 is published in volumes covering different regions of the United States:

- **Volume 1**: Semiarid Southwest (Arizona, Southeast California, Nevada, New Mexico, Utah)
- **Volume 2**: Ohio River Basin and Surrounding States
- **Volume 3**: Puerto Rico and the U.S. Virgin Islands
- **Volume 4**: Hawaiian Islands
- **Volume 5**: Selected Pacific Islands (American Samoa, Guam, Commonwealth of Northern Mariana Islands)
- **Volume 6**: California
- **Volume 7**: Alaska
- **Volume 8**: Midwestern States (Colorado, Iowa, Kansas, Michigan, Minnesota, Missouri, Montana, Nebraska, North Dakota, Oklahoma, South Dakota, Wisconsin, Wyoming)
- **Volume 9**: Southeastern States (Alabama, Arkansas, Florida, Georgia, Louisiana, Mississippi)
- **Volume 10**: Northeastern States (Connecticut, Delaware, District of Columbia, Illinois, Indiana, Kentucky, Maine, Maryland, Massachusetts, New Hampshire, New Jersey, New York, North Carolina, Ohio, Pennsylvania, Rhode Island, South Carolina, Tennessee, Vermont, Virginia, West Virginia)
- **Volume 11**: Texas

**Important**: Some states do not have Atlas 14 coverage, including **Oregon** and **Washington**. Attempts to download data for locations outside Atlas 14 project areas will raise a `ValueError` with information about the coverage limitation.

### Installation

The NOAA module is included with pfdf. No additional installation is required beyond installing the pfdf package.

```bash
pip install git+https://github.com/rogerlew/usgs-pfdf.git
```

### Basic Usage

```python
from pfdf.data.noaa import atlas14

# Download precipitation intensity data for Denver, Colorado
result = atlas14.download(
    lat=39.0,
    lon=-105.0,
    parent="./data",
    name="denver_intensity.csv",
    statistic='mean',
    data='intensity',
    series='pds',
    units='metric'
)

print(f"Data saved to: {result}")
```

### Parameters

#### `download(lat, lon, **kwargs)`

Downloads precipitation frequency estimates for a given location.

**Required Parameters:**
- `lat` (float): Latitude in decimal degrees (-90 to 90)
- `lon` (float): Longitude in decimal degrees (-180 to 180)

**Optional Parameters:**

*File Options:*
- `parent` (str or Path): Parent directory for the downloaded file. Defaults to current directory.
- `name` (str): Name for the downloaded file. Defaults to auto-generated name based on parameters.
- `overwrite` (bool): Whether to overwrite existing files. Defaults to `False`.

*Data Options:*
- `statistic` (str): Which PFE statistic to download
  - `'mean'`: Mean PFE values (default)
  - `'upper'`: Upper bound of 90% confidence interval
  - `'lower'`: Lower bound of 90% confidence interval
  - `'all'`: Mean, upper, and lower bounds

- `data` (str): Type of precipitation data
  - `'intensity'`: Precipitation intensity in mm/hour or inches/hour (default)
  - `'depth'`: Precipitation depth in mm or inches

- `series` (str): Time series type for PFE estimation
  - `'pds'`: Partial duration series (default)
  - `'ams'`: Annual maximum series

- `units` (str): Units for the returned data
  - `'metric'`: mm or mm/hour (default)
  - `'english'`: inches or inches/hour

*HTTP Options:*
- `timeout` (int, float, or tuple): Maximum time in seconds to wait for server response. Can be a single value or (connect_timeout, read_timeout). Defaults to 10 seconds.

**Returns:**
- `Path`: Path object pointing to the downloaded CSV file

**Raises:**
- `ValueError`: If location is outside Atlas 14 coverage area
- `requests.exceptions.HTTPError`: If server returns an error
- `requests.exceptions.Timeout`: If request exceeds timeout duration

### Usage Examples

#### Download Precipitation Intensity

```python
from pfdf.data.noaa import atlas14

# Download mean precipitation intensity for a location
path = atlas14.download(
    lat=39.7392,
    lon=-104.9903,
    parent="./precipitation_data",
    statistic='mean',
    data='intensity',
    series='pds',
    units='metric'
)
```

#### Download Precipitation Depth

```python
from pfdf.data.noaa import atlas14

# Download precipitation depth estimates
path = atlas14.download(
    lat=34.0522,
    lon=-118.2437,
    parent="./precipitation_data",
    name="los_angeles_depth.csv",
    statistic='mean',
    data='depth',
    series='pds',
    units='metric'
)
```

#### Download All Statistics (Mean, Upper, Lower)

```python
from pfdf.data.noaa import atlas14

# Download mean, upper, and lower bound estimates
path = atlas14.download(
    lat=41.8781,
    lon=-87.6298,
    parent="./precipitation_data",
    name="chicago_all_stats.csv",
    statistic='all',
    data='intensity',
    series='pds',
    units='metric'
)
```

#### Use English Units

```python
from pfdf.data.noaa import atlas14

# Download data in inches/hour instead of mm/hour
path = atlas14.download(
    lat=30.2672,
    lon=-97.7431,
    parent="./precipitation_data",
    name="austin_english.csv",
    statistic='mean',
    data='intensity',
    series='pds',
    units='english'
)
```

#### Handle Locations Without Coverage

```python
from pfdf.data.noaa import atlas14

try:
    # Oregon does not have Atlas 14 coverage
    path = atlas14.download(
        lat=45.5152,
        lon=-122.6784,  # Portland, OR
        statistic='mean',
        data='intensity'
    )
except ValueError as e:
    print(f"Error: {e}")
    # Output: NOAA Atlas 14 data is not available for this location...
    # Handle the error appropriately for your application
```

### Output Format

The downloaded CSV file contains precipitation frequency estimates organized by duration and return period. Example output:

```
Point precipitation frequency estimates (millimeters/hour)
NOAA Atlas 14 Volume 8 Version 2
Data type: Precipitation intensity
Time series type: Partial duration
Project area: Midwestern States
Location name (ESRI Maps): None
Station Name: None
Latitude: 39.0 Degree
Longitude: -105.0 Degree
Elevation (USGS): None None


PRECIPITATION FREQUENCY ESTIMATES
by duration for ARI (years):, 1,2,5,10,25,50,100,200,500,1000
5-min:, 73,88,116,140,176,205,237,270,316,353
10-min:, 53,65,85,103,129,150,173,198,231,259
15-min:, 43,53,69,83,105,122,141,161,188,210
30-min:, 28,35,45,55,69,80,92,105,123,137
60-min:, 18,21,27,32,40,48,55,64,76,85
2-hr:, 10,12,15,18,23,28,32,37,45,51
3-hr:, 8,9,11,13,17,20,24,28,33,38
6-hr:, 5,6,7,8,10,12,15,17,21,24
12-hr:, 3,4,4,5,7,8,9,11,13,15
24-hr:, 2,2,3,3,4,5,6,7,8,9
...
```

The data includes:
- **Header**: Metadata about the location and data type
- **Estimates Table**: Rows for different durations (5-min to 60-day), columns for different annual recurrence intervals (ARI) in years

### Error Handling

The module provides clear error messages for common issues:

#### Location Outside Coverage Area

```python
ValueError: NOAA Atlas 14 data is not available for this location
(lat=45.5152, lon=-122.6784). Error 3.0: Selected location is not
within a project area. Atlas 14 coverage varies by region - some areas
like Oregon and Washington do not have Atlas 14 precipitation frequency
estimates available.
```

#### Connection Timeout

```python
requests.exceptions.ConnectTimeout: Took too long to connect to the
NOAA PFDS server. Try checking:
  * If your internet connection is down
  * If NOAA PFDS is down
If a connection is down, then wait a bit and try again later.
Otherwise, try increasing "timeout" to a longer interval.
```

#### Server Response Timeout

```python
requests.exceptions.ReadTimeout: The NOAA PFDS server took too long to
respond. Try checking:
  * If NOAA PFDS is down
If a connection is down, then wait a bit and try again later.
Otherwise, try increasing "timeout" to a longer interval.
```

### API Reference

#### Functions

##### `base_url()`

Returns the base URL for the NOAA Atlas 14 data API.

**Returns:** `str` - Base URL for the Atlas 14 API

**Example:**
```python
from pfdf.data.noaa import atlas14

url = atlas14.base_url()
print(url)  # https://hdsc.nws.noaa.gov/cgi-bin/hdsc/new
```

##### `query_url(statistic='mean')`

Returns the complete query URL for a specific PFE statistic.

**Parameters:**
- `statistic` (str): The statistic to query ('mean', 'upper', 'lower', or 'all')

**Returns:** `str` - Full query URL

**Example:**
```python
from pfdf.data.noaa import atlas14

mean_url = atlas14.query_url('mean')
upper_url = atlas14.query_url('upper')
lower_url = atlas14.query_url('lower')
all_url = atlas14.query_url('all')
```

##### `download(lat, lon, **kwargs)`

Downloads precipitation frequency estimate data for a location. See [Parameters](#parameters) section for full details.

## Advanced Usage

### Custom Timeout Configuration

For slow connections or large requests, you can configure custom timeout settings:

```python
from pfdf.data.noaa import atlas14

# Single timeout value (applies to both connect and read)
path = atlas14.download(
    lat=39.0,
    lon=-105.0,
    timeout=60  # 60 seconds
)

# Separate connect and read timeouts
path = atlas14.download(
    lat=39.0,
    lon=-105.0,
    timeout=(10, 30)  # 10 seconds to connect, 30 seconds to read
)

# No timeout (not recommended - may hang indefinitely)
path = atlas14.download(
    lat=39.0,
    lon=-105.0,
    timeout=None
)
```

### Batch Processing

For processing multiple locations:

```python
from pfdf.data.noaa import atlas14
from pathlib import Path

locations = [
    {"name": "Denver", "lat": 39.7392, "lon": -104.9903},
    {"name": "Chicago", "lat": 41.8781, "lon": -87.6298},
    {"name": "Austin", "lat": 30.2672, "lon": -97.7431},
]

output_dir = Path("./precipitation_data")
output_dir.mkdir(exist_ok=True)

for loc in locations:
    try:
        path = atlas14.download(
            lat=loc["lat"],
            lon=loc["lon"],
            parent=output_dir,
            name=f"{loc['name']}_atlas14.csv",
            statistic='mean',
            data='intensity',
            series='pds',
            units='metric',
            overwrite=True
        )
        print(f"✓ Downloaded data for {loc['name']}")
    except ValueError as e:
        print(f"✗ {loc['name']}: No Atlas 14 coverage - {e}")
    except Exception as e:
        print(f"✗ {loc['name']}: Error - {e}")
```

## References

Bonnin, G.M., Martin, D., Lin, B., Parzybok, T., Yekta, M., and Riley, D., 2006, Precipitation-Frequency Atlas of the United States, NOAA Atlas 14, Volume 1, Version 5.0: Semiarid Southwest (Arizona, Southeast California, Nevada, New Mexico, Utah), National Weather Service, Silver Spring, Maryland.

Perica, S., and others, 2013, Precipitation-Frequency Atlas of the United States, NOAA Atlas 14, Volume 9, Version 2.0: Southeastern States (Alabama, Arkansas, Florida, Georgia, Louisiana, Mississippi), National Weather Service, Silver Spring, Maryland.

Perica, S., and others, 2015, Precipitation-Frequency Atlas of the United States, NOAA Atlas 14, Volume 10, Version 1.0: Northeastern States (Connecticut, Delaware, District of Columbia, Illinois, Indiana, Kentucky, Maine, Maryland, Massachusetts, New Hampshire, New Jersey, New York, North Carolina, Ohio, Pennsylvania, Rhode Island, South Carolina, Tennessee, Vermont, Virginia, West Virginia), National Weather Service, Silver Spring, Maryland.

For a complete list of Atlas 14 volumes and references, visit: https://hdsc.nws.noaa.gov/hdsc/pfds/

## Data Attribution

Data provided by the NOAA National Weather Service, Hydrometeorological Design Studies Center (HDSC). When using Atlas 14 data in publications, please cite the appropriate volume for your region of interest.

## Support

For issues related to this module, please report them at: https://github.com/rogerlew/usgs-pfdf/issues

For questions about the Atlas 14 dataset itself, contact NOAA HDSC: https://hdsc.nws.noaa.gov/hdsc/hdsc_about.html
