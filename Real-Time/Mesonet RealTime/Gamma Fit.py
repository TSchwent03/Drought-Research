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


def spi_gamma_params(spi_dict):
    gamma_params_by_location_month = {} # Dictionary to store gamma parameters by location and month

    for location_name, monthly_data in spi_dict.items(): # Loop through locations
        gamma_params_by_month_for_location = {} # Dictionary to store monthly params for THIS location
        for month, rainfall_series in monthly_data.items(): # Loop through months for EACH location
            params = stats.gamma.fit(rainfall_series, floc=-0.0000000001) # Fit gamma, fix location at -0.0000000001
            alpha, loc, beta = params
            gamma_params_by_month_for_location[month] = {'alpha': alpha, 'beta': beta} # Store monthly params
            print(f"Gamma fit for {location_name}, {month} rainfall: alpha={alpha:.4f}, beta={beta:.4f}")
        gamma_params_by_location_month[location_name] = gamma_params_by_month_for_location # Store monthly params for LOCATION

    return gamma_params_by_location_month


def calculate_cumulative_rainfall(historical_rainfall_data, timescale):
    """
    Calculates cumulative rainfall for a given timescale (in months) from historical monthly data.
    Allows for unequal data lengths by considering available data for each cumulative period.

    Args:
        historical_rainfall_data (dict): Nested dictionary of historical rainfall data.
        timescale (int): Timescale in months (e.g., 3, 6, 12).

    Returns:
        dict: Nested dictionary of cumulative rainfall data.
    """
    cumulative_rainfall_data = {}
    for location_name, monthly_data in historical_rainfall_data.items():
        cumulative_rainfall_data[location_name] = {}
        months = list(monthly_data.keys())
        month_order = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
        ordered_months = [m for m in month_order if m in months]

        for start_month_index, start_month in enumerate(ordered_months):
            cumulative_series = []
            min_period_length = float('inf') # Initialize to infinity for shortest period length

            # Determine shortest data length within the timescale window for this starting month
            for month_offset in range(timescale):
                month_name = ordered_months[(start_month_index + month_offset) % 12]
                month_data = monthly_data[month_name]
                min_period_length = min(min_period_length, len(month_data))

            for i in range(min_period_length): # Loop up to the shortest length in the period
                cumulative_sum = 0
                for month_offset in range(timescale):
                    month_name = ordered_months[(start_month_index + month_offset) % 12]
                    month_data = monthly_data[month_name]
                    cumulative_sum += month_data[i] # Use index 'i' - now valid for all months in period
                cumulative_series.append(round(cumulative_sum, 2))
            cumulative_rainfall_data[location_name][start_month] = cumulative_series
    return cumulative_rainfall_data


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
def new_spi_calculation(gamma_params, new_rainfall_data):
    calculated_spi_2025_locations = {} # Store SPI values by location

    for location_name, monthly_new_rainfall in new_rainfall_data.items(): # Loop through locations
        calculated_spi_for_location = {} # Store monthly SPIs for THIS location
        for month, new_rainfall in monthly_new_rainfall.items(): # Loop through months for EACH location
            location_month_gamma_params = gamma_params[location_name][month] # Get location-MONTH specific parameters
            spi_value = calculate_spi_from_rainfall(new_rainfall, (location_month_gamma_params['alpha'], 0, location_month_gamma_params['beta'])) # Use location-MONTH params
            calculated_spi_for_location[month] = spi_value
            print(f"For {location_name}, {month} 2025 rainfall of {new_rainfall:.2f} inches, SPI = {spi_value:.2f}")
        calculated_spi_2025_locations[location_name] = calculated_spi_for_location # Store monthly SPIs for LOCATION

def calculate_rainfall_from_spi(spi_value, gamma_params):
    """
    Calculates the rainfall amount corresponding to a given SPI value,
    using a fitted gamma distribution.

    Args:
        spi_value (float): The SPI value for which to calculate the rainfall amount.
        gamma_params (tuple): A tuple containing the fitted gamma distribution parameters
                                (alpha, loc, beta), where loc is assumed to be fixed at 0.

    Returns:
        float: The rainfall amount (in inches or the units of your historical data)
                corresponding to the given SPI value.
    """
    alpha, loc, beta = gamma_params

    # Convert SPI value back to cumulative probability (CDF) in standard normal distribution
    cumulative_probability = stats.norm.cdf(spi_value)

    # Handle edge cases (very low or very high SPIs - probabilities near 0 or 1)
    if cumulative_probability <= 0:
        return 0.0  # Or a very small rainfall value, or NaN if you prefer to indicate "no rainfall" for extreme SPI-
    if cumulative_probability >= 1:
        return np.inf # Or a very large rainfall value, or NaN if you prefer to indicate "effectively infinite rainfall" for extreme SPI+

    # Calculate rainfall amount using the Percent Point Function (PPF, inverse CDF) of the gamma distribution
    rainfall_amount = stats.gamma.ppf(cumulative_probability, a=alpha, loc=loc, scale=beta)

    return rainfall_amount

historical_data_dict = create_historical_rainfall_dict_from_csvs(r"C:\Users\thoma\Documents\GitHub\Drought-Research\Precip Data\Dataset B-a\Monthly Tot CSV")

one_month_rainfall_dict = calculate_cumulative_rainfall(historical_data_dict, 1)
three_month_rainfall_dict = calculate_cumulative_rainfall(historical_data_dict, 3)
six_month_rainfall_dict = calculate_cumulative_rainfall(historical_data_dict, 6)
twelve_month_rainfall_dict = calculate_cumulative_rainfall(historical_data_dict, 12)
gamma_params_by_location_one_month = spi_gamma_params(one_month_rainfall_dict)
gamma_params_by_location_three_month = spi_gamma_params(three_month_rainfall_dict)
gamma_params_by_location_six_month = spi_gamma_params(six_month_rainfall_dict)
gamma_params_by_location_twelve_month = spi_gamma_params(twelve_month_rainfall_dict)

# --- Save Gamma Parameters to CSV ---
def save_gamma_params_to_csv(gamma_params, file_path, timescale):
    data = []
    for location, monthly_params in gamma_params.items():
        for month, params in monthly_params.items():
            data.append({
                'Timescale': timescale,
                'Location': location,
                'Month': month,
                'Alpha': params['alpha'],
                'Beta': params['beta']
            })
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)
    print(f"Gamma parameters for {timescale}-month timescale saved to {file_path}")

# Example usage:
save_gamma_params_to_csv(gamma_params_by_location_one_month, r'C:\Users\thoma\Documents\GitHub\Drought-Research\Real-Time\Mesonet RealTime\gamma_params_1month.csv', 1)
save_gamma_params_to_csv(gamma_params_by_location_three_month, r'C:\Users\thoma\Documents\GitHub\Drought-Research\Real-Time\Mesonet RealTime\gamma_params_3month.csv', 3)
save_gamma_params_to_csv(gamma_params_by_location_six_month, r'C:\Users\thoma\Documents\GitHub\Drought-Research\Real-Time\Mesonet RealTime\gamma_params_6month.csv', 6)
save_gamma_params_to_csv(gamma_params_by_location_twelve_month, r'C:\Users\thoma\Documents\GitHub\Drought-Research\Real-Time\Mesonet RealTime\gamma_params_12month.csv', 12)

new_rainfall_data_2025_locations = { # New data now ALSO structured by location
    'St. Joseph, Buchanan County, MO': {
        'January': 2.1, # Inches of rainfall in January 2025 for Columbia, MO
        'February': 0.69
    }
}

# --- Example Usage (assuming you have gamma_params_by_location_month_timescale already calculated) ---
# Example: Get gamma parameters for January, 1-month SPI, for 'Albany, Gentry County, MO'
location_name_example = 'Albany, Gentry County, MO'
month_example = 'January'
gamma_params_example = (gamma_params_by_location_three_month[location_name_example][month_example]['alpha'],
                        0, # loc is fixed at 0
                        gamma_params_by_location_three_month[location_name_example][month_example]['beta'])

# Example SPI values representing different drought severity levels (from SPI classification table)
spi_values_to_check = [-2.0, -1.6, -1.3, -0.8, -0.5, 0.5, 0.8, 1.3, 1.6, 2.0] # Example range, include more as needed
severity_labels = ["Exceptional Drought", "Extreme Drought", "Severe Drought", "Moderate Drought", "Abnormally Dry", "Abnormally Wet", "Moderate Wet", "Severe Wet", "Extreme Wet", "Exceptional Wet"]

print(f"\nRainfall amounts corresponding to different SPI values for {location_name_example}, {month_example}, 3-month SPI:")
for i, spi_val in enumerate(spi_values_to_check):
    rainfall = calculate_rainfall_from_spi(spi_val, gamma_params_example)
    print(f"SPI = {spi_val:.2f} ({severity_labels[i]}): Rainfall = {rainfall:.2f} inches") # Adjust units if needed

# --- Loop through all locations and timescales to calculate rainfall from SPI ---
gamma_params_by_timescale = {
    1: gamma_params_by_location_one_month,
    3: gamma_params_by_location_three_month,
    6: gamma_params_by_location_six_month,
    12: gamma_params_by_location_twelve_month
}

print("\n--- Rainfall Amounts for Different SPI Values Across Locations and Timescales ---")

for timescale, gamma_params_for_ts in gamma_params_by_timescale.items():
    print(f"\n--- Timescale: {timescale}-Month SPI ---")
    for location_name, gamma_params_by_month in gamma_params_for_ts.items():
        print(f"\n-- Location: {location_name} --")
        for month, params in gamma_params_by_month.items():
            print(f"\n--- Month: {month} ---")
            for i, spi_val in enumerate(spi_values_to_check):
                gamma_params_tuple = (params['alpha'], 0, params['beta'])
                rainfall = calculate_rainfall_from_spi(spi_val, gamma_params_tuple)
                print(f"  SPI = {spi_val:.2f} ({severity_labels[i]}): Rainfall = {rainfall:.2f} inches")

# Assuming you have gamma_params_by_location_month_timescale and spi_values_to_check, severity_labels defined

output_file_path = r"C:\Users\thoma\Documents\GitHub\Drought-Research\Extension Paper\spi_to_rainfall_conversion.txt"

with open(output_file_path, 'w') as f:
    for timescale, gamma_params_for_ts in gamma_params_by_timescale.items():
        f.write(f"--- Timescale: {timescale}-Month SPI ---\n")
        for location_name, gamma_params_by_month in gamma_params_for_ts.items():
            f.write(f"\n-- Location: {location_name} --\n")
            for month, params in gamma_params_by_month.items():
                f.write(f"\n--- Month: {month} ---\n")
                for i, spi_val in enumerate(spi_values_to_check):
                    gamma_params_tuple = (params['alpha'], 0, params['beta'])
                    rainfall = calculate_rainfall_from_spi(spi_val, gamma_params_tuple)
                    f.write(f"  SPI = {spi_val:.2f} ({severity_labels[i]}): Rainfall = {rainfall:.2f} inches\n")

print(f"SPI to rainfall conversion data has been saved to: {output_file_path}")