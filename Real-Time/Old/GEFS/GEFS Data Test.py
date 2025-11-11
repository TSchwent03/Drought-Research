import requests
import cfgrib
import xarray as xr

# Step 1: Define Point Location
latitude = 38.9
longitude = -92.3

# Step 2: Forecast Cycle and Hour (Example: 00Z cycle, 3-hour forecast)
forecast_cycle_year_month_day = "20250210"  # YYYYMMDD format - Replace with current or desired date
forecast_cycle_hour = "00"             # HH format (00, 06, 12, 18)
forecast_hour = "003"                  # Forecast hour (e.g., "003" for 3-hour, "024" for 24-hour)

# Step 3: Construct URL (Example - ADJUST BASED ON NOMADS DIRECTORY STRUCTURE)
base_url = "https://nomads.ncep.noaa.gov/pub/data/nccf/com/gens/prod/"
url =  r"C:\Users\thoma\Downloads\geavg.t12z.pgrb2a.0p50.f198"  #f"{base_url}gefs.{forecast_cycle_year_month_day}/{forecast_cycle_hour}/atmos/pgrb2ap5/gefs.t{forecast_cycle_hour}z.pgrb2a.p5.f{forecast_hour}"

print(f"Downloading data from: {url}")

# Step 4: Download GRIB2 file
#response = requests.get(url)
#response.raise_for_status() # Raise an exception for bad status codes

#with open("gefs_data.grib2", 'wb') as f:
    #f.write(response.content)

#print("GRIB2 data downloaded.")

# Step 5: Parse GRIB2 and Extract Data
try:
    ds = xr.open_dataset(r"C:\Users\thoma\Downloads\geavg.t12z.pgrb2a.0p50.f198", engine="cfgrib") # Using cfgrib engine
    print("GRIB2 file opened as xarray Dataset.")

    # **IMPORTANT:** You need to find the correct variable name for accumulated precipitation in your GEFS file.
    # Use ds.variables or ds.data_vars to inspect the variable names in the dataset.
    # Common names might be 'tp', 'APCP', 'Total Precipitation', etc.  (This varies by model and variable definition)

    precipitation_variable_name = 'tp' # **<-- REPLACE with the actual variable name!**

    # Select the precipitation variable
    precipitation_data = ds[precipitation_variable_name]

    # Find the nearest grid point to your lat/lon
    point_data = precipitation_data.sel(latitude=latitude, longitude=longitude, method='nearest') # or method='ffill', 'bfill'

    # Get the precipitation value (assuming units are in meters of water equivalent - check the GRIB metadata)
    precipitation_value = point_data.values

    print(f"Precipitation at latitude {latitude}, longitude {longitude}: {precipitation_value} meters (check units!)")


except Exception as e:
    print(f"Error processing GRIB2 file: {e}")

print("Done.")