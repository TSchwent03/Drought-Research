from datetime import date, timedelta
import os
import datetime

def process_file(filename):

  # Declaring base variables
  start_date = None
  end_date = None
  max_value = float("-inf")
  min_value = float("inf")
  missing_dates = []
  previous_date = None

  try:
    with open(filename, 'r') as file:
      for line in file:
        try:
          # Split the line into components (month, day, year, data)
          # Expected format: MM DD YYYY VALUE
          month, day, year, data_value = line.strip().split()

          # Convert month, day, year to integers and data to float
          month = int(month)
          day = int(day)
          year = int(year)
          data_value = float(data_value)

        except ValueError:
          # Skip lines with invalid data format or conversion errors (e.g. headers)
          print(f"Skipping invalid line in {filename}")
          continue

        # Create date object for the current line
        line_date = date(year, month, day)

        # Update date range
        if start_date is None or line_date < start_date:
          start_date = line_date
        if end_date is None or line_date > end_date:
          end_date = line_date

        # Update min/max values
        max_value = max(max_value, data_value)
        min_value = min(min_value, data_value)

        # Check for missing days between entries (assuming chronological order)
        # If the current date is not exactly one day after the previous date, we have a gap.
        if previous_date is not None and line_date != previous_date + timedelta(days=1):
          missing_dates.extend(get_missing_dates(previous_date, line_date))

        previous_date = line_date

  except FileNotFoundError:
    print(f"File not found: {filename}")
    return None, None, None, None, None

  return start_date, end_date, max_value, min_value, missing_dates

def get_missing_dates(start_date, end_date):
  missing_dates = []
  # Start checking from the day after the start_date
  current_date = start_date + timedelta(days=1)

  # Loop until we reach the end_date
  while current_date < end_date:
    missing_dates.append(current_date)
    current_date += timedelta(days = 1)

  return missing_dates

def write_file(data_folder, output_filename):
  with open(output_filename, 'w') as output_file:
    output_file.write("Data Summary\n\n")

    # Iterate through all files in the data folder
    for filename in os.listdir(data_folder):
      if filename.endswith(".txt"):  # Check for files with .txt extension
        full_path = os.path.join(data_folder, filename)
        
        # Process the individual file to get stats
        first_date, last_date, highest, lowest, missing_days = process_file(full_path)

        # If processing was successful (dates found)
        if first_date and last_date:
          output_file.write(f"File: {filename}\n")
          output_file.write(f"First Date: {first_date.strftime('%Y-%m-%d')}\n")
          output_file.write(f"Last Date: {last_date.strftime('%Y-%m-%d')}\n")
          output_file.write(f"Highest Value: {highest:.2f}\n")  # Format with 2 decimal places 
          output_file.write(f"Lowest Value: {lowest:.2f}\n")

          # List specific missing dates if any exist
          if missing_days:
            output_file.write("Missing Dates:\n")
            for date in missing_days:
              output_file.write(f"- {date.strftime('%Y-%m-%d')}\n")
          
          output_file.write("\n")  # Add a blank line between file summaries

        # Handle the case where the script reads its own output file if in same dir
        elif filename == "data_summary.txt":
          output_file.write("")
  
        else:
          output_file.write(f"Error processing file: {filename}\n\n")

def main():
  # Replace 'data_folder' with the actual path to your folder containing data files
  program_path = os.path.dirname(os.path.abspath(__file__))

  # Construct absolute path to the input data folder
  rel_data_folder = r'Precip Data\Dataset B-a\Daily Raw'
  data_folder = os.path.abspath(os.path.join(program_path, "..", "..", rel_data_folder))

  # Construct absolute path to the output folder
  rel_output_folder = r'Precip Data\Dataset B-a\Daily QC'
  output_folder = os.path.abspath(os.path.join(program_path, "..", "..", rel_output_folder))

  # Generate output filename with current date
  now = datetime.datetime.now()
  today_str = now.strftime("%Y-%m-%d")
  file_name = f'data_summary_{today_str}.txt'
  output_filename = os.path.join(output_folder, file_name)

  # Run the report generation
  write_file(data_folder, output_filename)

if __name__ == "__main__":
  main()
