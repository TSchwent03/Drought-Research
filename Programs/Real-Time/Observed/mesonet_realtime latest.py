import requests
from bs4 import BeautifulSoup
import datetime
import sys 
import csv
import os 

# Define a dictionary mapping station codes to full locations
stations = {
    "alb": "Albany, Gentry County, MO",
    "aux": "Auxvasse, Audrain County, MO",
    "bwk": "Brunswick, Carroll County, MO",
    "crd": "Cardwell, Dunklin County, MO",
    "chs": "Charleston, Mississippi County, MO",
    "clk": "Clarkton, Dunklin County, MO",
    "san": "Columbia-Sanborn Field, Boone County, MO",
    "sfm": "Columbia-South Farms, Boone County, MO",
    "wur": "Cook Station, Crawford County, MO",
    "crn": "Corning, Atchison County, MO",
    "del": "Delta, Cape Girardeau County, MO",
    "gln": "Glennonville, Dunklin County, MO",
    "lee": "Hayward, Pemiscot County, MO",
    "lam": "Lamar, Barton County, MO",
    "lin": "Linneus, Linn County, MO",
    "mon": "Monroe City, Monroe County, MO",
    "nov": "Novelty, Knox County, MO",
    "pvl": "Portageville, Pemiscot County, MO",
    "stj": "St. Joseph, Buchanan County, MO",
}

def fetch_data(start_month, end_month, start_day, end_day, start_year, end_year):
    results = []
    for station_code, station_name in stations.items():
        url = f"http://agebb.missouri.edu/weather/history/report.asp?station_prefix={station_code}&start_month={start_month}&end_month={end_month}&start_day={start_day}&end_day={end_day}&start_year={start_year}&end_year={end_year}&period_type=1&convert=1&field_elements=70"
        response = requests.get(url)
        response.raise_for_status()
        html_content = response.content

        soup = BeautifulSoup(html_content, "html.parser")
        pre_tag = soup.find("pre")

        if pre_tag:
            data_text = pre_tag.text.strip()
            total_line = None # Initialize to avoid potential reference before assignment
            for line in data_text.split("\n"):
                if "Total" in line:
                    total_line = line
                    break
            if total_line:
                total_precipitation = total_line.split()[-1]
                # Return structured data instead of a formatted string
                results.append({'station_name': station_name, 'station_code': station_code, 'total_precipitation': total_precipitation})
    return results

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
output_directory = script_dir # Save output in the same directory as the script

# Get current date
now = datetime.datetime.now()

# Define the output filename
today_str = now.strftime("%Y-%m-%d")
txt_output_filename = f"weather_terminal_output_{today_str}.txt"
csv_output_filename = f"weather_data_{today_str}.csv"

# --- Construct the full path ---
txt_output_filepath = os.path.join(output_directory, txt_output_filename)
csv_output_filepath = os.path.join(output_directory, csv_output_filename)

# Store the original standard output
original_stdout = sys.stdout

try:
    # Open both the text and CSV files for writing
    with open(txt_output_filepath, 'w', encoding='utf-8') as f, \
         open(csv_output_filepath, 'w', newline='', encoding='utf-8') as csvfile:
        
        csv_writer = csv.writer(csvfile)
        # Write CSV Header
        csv_writer.writerow(['Period', 'Start Date', 'End Date', 'Station Name', 'Station Code', 'Total Precipitation (in)'])

        # Redirect standard output to the file
        sys.stdout = f

        # --- All your original printing logic goes here ---
        # Get current date
        now = datetime.datetime.now()
        print(f"Report generated on: {now.strftime('%Y-%m-%d %H:%M:%S')}\n") # Example of adding info

        # Define periods
        periods = [
            ("Past Month", 1),
            ("Past 3 Months", 3),
            ("Past 6 Months", 6),
            ("Past 12 Months", 12),
        ]

        # Fetch and print data for each period
        for period_name, months_ago in periods:
            print(f"\n{period_name}:") # This print goes to the file

            # Determine start and end dates (using the same logic as before)
            end_date_calc = now.replace(day=1) - datetime.timedelta(days=1)
            end_month = end_date_calc.month
            end_day = end_date_calc.day
            end_year = end_date_calc.year

            start_date_calc = end_date_calc.replace(day=1)
            for _ in range(months_ago - 1):
                start_date_calc = (start_date_calc - datetime.timedelta(days=1)).replace(day=1)

            start_month = start_date_calc.month
            start_day = start_date_calc.day
            start_year = start_date_calc.year

            start_date_str = f"{start_year}-{start_month:02d}-{start_day:02d}"
            end_date_str = f"{end_year}-{end_month:02d}-{end_day:02d}"

            print(f"Period Range: {start_date_str} to {end_date_str}") # This print goes to the file

            # Call fetch_data with calculated date parameters
            # ** Use the version of fetch_data that returns formatted strings **
            results = fetch_data(start_month, end_month, start_day, end_day, start_year, end_year)

            # Print results (these prints will now go to the file)
            # And write to CSV
            if not results:
                print("  No data fetched for this period.")
            else:
                for result in results:
                    # Write to text file
                    print(f"  {result['station_name']} ({result['station_code']}): {result['total_precipitation']}")
                    # Write to CSV file
                    csv_writer.writerow([period_name, start_date_str, end_date_str, result['station_name'], result['station_code'], result['total_precipitation']])
                    
        print(f"\n--- End of Report ---") # Final message in the file

except Exception as e:
    # If an error occurs, make sure to restore stdout before printing the error to console
    sys.stdout = original_stdout
    print(f"\n--- SCRIPT ERROR ---")
    print(f"An error occurred: {e}")
    print(f"Output may be incomplete.")
    # Optional: re-raise e
finally:
    # --- Crucial: Restore original standard output ---
    # This ensures any prints *after* this block go back to the console
    sys.stdout = original_stdout

# This final print will appear on your console screen, not in the file
print(f"Script finished. Output saved to {txt_output_filename} and {csv_output_filename}")