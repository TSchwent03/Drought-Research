import scipy.stats as stats
import numpy as np
import pandas as pd
import os

# --- Phase 1: Fit Gamma Distributions to Historical Rainfall Data ---

# Historical Monthly Rainfall Data
def create_historical_rainfall_dict_from_csvs(csv_directory):
    """
    Reads rainfall data from multiple CSV files in a directory and
    organizes it into the historical_rainfall_data dictionary structure.

    Args:
        csv_directory (str): Path to the directory containing the CSV files.

    Returns:
        dict: historical_rainfall_data dictionary (nested dictionary of location, month, rainfall data).
              Returns an empty dictionary if no CSV files are found or if errors occur.
    """
    historical_rainfall_data = {}
    csv_files = [f for f in os.listdir(csv_directory) if f.endswith('.csv')] # Get list of CSV files

    if not csv_files:
        print(f"Warning: No CSV files found in directory: {csv_directory}")
        return {}

    for csv_file in csv_files:
        try:
            # 1. Extract location name from filename (adjust as needed for your filenames)
            location_name = csv_file.replace('_totals.csv', '') # Basic cleaning - customize as needed
            location_name = location_name.replace('_', ' ') # Replace underscores with spaces for nicer location names if needed

            # 2. Read CSV into pandas DataFrame
            file_path = os.path.join(csv_directory, csv_file)
            df = pd.read_csv(file_path)

            # 3. Create month-specific rainfall list for this location
            monthly_rainfall_data = {}
            for index, row in df.iterrows():
                year = row['Year'] # Assuming column name is 'Year' - adjust if different
                month = row['Month'] # Assuming column name is 'Month' - adjust if different
                total_rainfall = row['Total'] # Assuming column name is 'Total' - adjust if different

                month_name_str = pd.Timestamp(year=int(year), month=int(month), day=1).strftime('%B') # Get full month name (e.g., "January")

                if month_name_str not in monthly_rainfall_data:
                    monthly_rainfall_data[month_name_str] = [] # Initialize list if month not yet in dict
                monthly_rainfall_data[month_name_str].append(float(total_rainfall)) # Append rainfall, convert to float

            # 4. Store monthly rainfall data for this location in the main dictionary
            historical_rainfall_data[location_name] = monthly_rainfall_data

            print(f"Processed CSV file: {csv_file} for location: {location_name}")

        except Exception as e:
            print(f"Error processing CSV file: {csv_file}. Skipping this file. Error: {e}")

    return historical_rainfall_data

historical_data_dict = create_historical_rainfall_dict_from_csvs(r"C:\Users\thoma\Documents\GitHub\Drought-Research\Precip Data\Dataset B-a\Monthly Tot CSV")

gamma_params_by_location_month = {} # Dictionary to store gamma parameters by location and month

for location_name, monthly_data in historical_data_dict.items(): # Loop through locations
    gamma_params_by_month_for_location = {} # Dictionary to store monthly params for THIS location
    for month, rainfall_series in monthly_data.items(): # Loop through months for EACH location
        params = stats.gamma.fit(rainfall_series, floc=-0.0000000001) # Fit gamma, fix location at 0
        alpha, loc, beta = params
        gamma_params_by_month_for_location[month] = {'alpha': alpha, 'beta': beta} # Store monthly params
        print(f"Gamma fit for {location_name}, {month} rainfall: alpha={alpha:.4f}, beta={beta:.4f}")
    gamma_params_by_location_month[location_name] = gamma_params_by_month_for_location # Store monthly params for LOCATION

# --- Phase 2: Function to Calculate SPI from Rainfall using Fitted Gamma Distribution (RE-USED FOR NEW DATA) ---

def calculate_spi_from_rainfall(rainfall_amount, gamma_params):

    alpha, loc, beta = gamma_params

    if rainfall_amount < 0: # Rainfall cannot be negative, handle if needed
        rainfall_amount = 0

    # Calculate cumulative probability (CDF) using the fitted gamma distribution
    cumulative_probability = stats.gamma.cdf(rainfall_amount, a=alpha, loc=loc, scale=beta)

    # Adjust CDF for SPI calculation (accounts for zero precipitation probability)
    if cumulative_probability == 0:
        spi_value = -np.inf # Or a very large negative number, depending on convention
    else:
        spi_value = stats.norm.ppf(cumulative_probability) # Convert CDF to standard normal (SPI)

    return spi_value


# --- Phase 3: Example - Calculate SPI for NEW rainfall data (using pre-calculated gamma parameters) ---

# new_rainfall_data_2025_locations = { # New data now ALSO structured by location
#     'Location1_Name': {
#         'January': 2.1, # Inches of rainfall in January 2025 for Columbia, MO
#         'February': 0.69
#     }
# }

# calculated_spi_2025_locations = {} # Store SPI values by location

# for location_name, monthly_new_rainfall in new_rainfall_data_2025_locations.items(): # Loop through locations
#     calculated_spi_for_location = {} # Store monthly SPIs for THIS location
#     for month, new_rainfall in monthly_new_rainfall.items(): # Loop through months for EACH location
#         location_month_gamma_params = gamma_params_by_location_month[location_name][month] # Get location-MONTH specific parameters
#         spi_value = calculate_spi_from_rainfall(new_rainfall, (location_month_gamma_params['alpha'], 0, location_month_gamma_params['beta'])) # Use location-MONTH params
#         calculated_spi_for_location[month] = spi_value
#         print(f"For {location_name}, {month} 2025 rainfall of {new_rainfall:.2f} inches, SPI = {spi_value:.4f}")
#     calculated_spi_2025_locations[location_name] = calculated_spi_for_location # Store monthly SPIs for LOCATION

# print("\nCalculated SPI values for 2025 (by location):", calculated_spi_2025_locations)