import os
import pandas as pd

def convert_excel_to_csv(input_folder, output_folder):
  """
  Converts Excel files in an input folder to CSV files in an output folder.

  Args:
    input_folder: Path to the input folder containing Excel files.
    output_folder: Path to the output folder for CSV files.
  """

  for file in os.listdir(input_folder):
    if file.endswith('.xlsx'):
      input_file = os.path.join(input_folder, file)
      output_file = os.path.join(output_folder, file.replace('.xlsx', '.csv'))
      try:
        df = pd.read_excel(input_file, header=None, skiprows=2, engine='openpyxl')
        df.to_csv(output_file, index=False)
      except (ValueError, zipfile.BadZipFile, PermissionError) as e:
        print(f"Error processing file {file}: {e}")

# Example usage:
input_folder = r'C:\Users\thoma\Documents\GitHub\Drought-Research\Precip Data\Dataset B\Monthly Tot SPI w Drgt Stats Excel'
output_folder = r'C:\Users\thoma\Documents\GitHub\Drought-Research\Precip Data\Dataset B\Monthly Tot SPI w Drgt Stats CSV'
convert_excel_to_csv(input_folder, output_folder)