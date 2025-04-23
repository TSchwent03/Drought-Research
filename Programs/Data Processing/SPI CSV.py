import pandas as pd
import os
import requests
import json

def extract_location(filename):
  """Extracts location from filename."""
  location = filename.split('_')[0]
  return location

def process_file(file_path):
  """
  Reads CSV, extracts location from filename, performs geocoding, and adds location as a column.

  Args:
      file_path: Path to the CSV file.

  Returns:
      A Pandas DataFrame with location added.
  """
  df = pd.read_csv(file_path)
  location = extract_location(os.path.basename(file_path))  # Extract from filename
  df['Location'] = get_location(location)  # Geocode and add location
  return df

def merge_csvs(input_folder, output_file):
  """
  Merges multiple CSV files into a single CSV with desired format.

  Args:
      input_folder: Path to the input folder containing CSV files.
      output_file: Path to the output CSV file.
  """
  data = []
  for file in os.listdir(input_folder):
    if file.endswith('.csv'):
      file_path = os.path.join(input_folder, file)
      df = process_file(file_path)
      if df is not None:
        df['file_name'] = file  # Add file name as a column (optional)
        data.append(df)
  combined_df = pd.concat(data, ignore_index=True)
  combined_df = combined_df[['Location', 'Date', 'spi1', 'spi3', 'spi6', 'spi12']]
  combined_df.to_csv(output_file, index=False)

def get_location(city_name):
    url = f"https://nominatim.openstreetmap.org/search?q={city_name}&format=json"
    response = requests.get(url)
    data = response.json()
    try:
        latitude = data[0]['lat']
        longitude = data[0]['lon']
        return latitude, longitude
    except (IndexError, KeyError):
        return None

# Example usage:
input_folder = r'C:\Users\thoma\Documents\GitHub\Drought-Research\Precip Data\Dataset B\Monthly Tot SPI w Drgt Stats CSV'
output_file = r'C:\Users\thoma\Documents\GitHub\Drought-Research\Precip Data\Dataset B\CSVs\SPI\combined_data.csv'
merge_csvs(input_folder, output_file)