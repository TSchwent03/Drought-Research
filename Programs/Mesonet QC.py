from datetime import date, timedelta
import os

def process_file(filename):
  """
  This function processes a single file and returns information about dates and data.

  Args:
      filename: The path to the file.

  Returns:
      A tuple containing:
          - first_date (datetime.date object): First date encountered in the file.
          - last_date (datetime.date object): Last date encountered in the file.
          - highest_value (float): Highest data value found.
          - lowest_value (float): Lowest data value found.
          - missing_dates (list): List of missing dates (datetime.date objects).
  """

  first_date = None
  last_date = None
  highest_value = float("-inf")
  lowest_value = float("inf")
  missing_dates = []
  previous_date = None

  try:
    with open(filename, 'r') as file:
      for line in file:
        try:
          # Split the line into components (month, day, year, data)
          month, day, year, data_value = line.strip().split()
          # Convert month, day, year to integers and data to float
          month = int(month)
          day = int(day)
          year = int(year)
          data_value = float(data_value)
        except ValueError:
          # Skip lines with invalid data format or conversion errors
          continue

        # Update date and data values
        current_date = date(year, month, day)
        if first_date is None or current_date < first_date:
          first_date = current_date
        if last_date is None or current_date > last_date:
          last_date = current_date
        highest_value = max(highest_value, data_value)
        lowest_value = min(lowest_value, data_value)

        # Check for missing days between entries (assuming chronological order)
        if previous_date is not None and current_date != previous_date + timedelta(days=1):
          missing_dates.extend(get_missing_dates(previous_date, current_date - timedelta(days=1)))

        previous_date = current_date

  except FileNotFoundError:
    print(f"Error: File '{filename}' not found.")
    return None, None, None, None, None

  return first_date, last_date, highest_value, lowest_value, missing_dates

def get_missing_dates(start_date, end_date):
  """
  This helper function generates a list of missing dates between two dates
  (inclusive) assuming chronological order.

  Args:
      start_date: The starting date (datetime.date object).
      end_date: The ending date (datetime.date object).

  Returns:
      A list of missing dates (datetime.date objects) between start and end date.
  """

  missing_dates = []
  current_date = start_date
  while current_date <= end_date:
    missing_dates.append(current_date)
    current_date += timedelta(days = 1)
  return missing_dates[1:]  # Remove the starting date (already processed)

def main():
  """
  This function processes all files in a folder and writes results to a text file.
  """

  # Replace 'data_folder' with the actual path to your folder containing data files
  data_folder = r'C:\Users\thoma\Documents\GitHub\Drought-Research\Programs\Data QC Samples\Mesonet'
  output_filename = r'C:\Users\thoma\Documents\GitHub\Drought-Research\Programs\Data QC Samples\Mesonet\data_summary.txt'

  with open(output_filename, 'w') as output_file:
    output_file.write("Data Summary\n\n")
    for filename in os.listdir(data_folder):
      if filename.endswith(".txt"):  # Check for files with .txt extension
        full_path = os.path.join(data_folder, filename)
        first_date, last_date, highest, lowest, missing_days = process_file(full_path)

        if first_date and last_date:
          output_file.write(f"File: {filename}\n")
          output_file.write(f"First Date: {first_date.strftime('%Y-%m-%d')}\n")
          output_file.write(f"Last Date: {last_date.strftime('%Y-%m-%d')}\n")
          output_file.write(f"Highest Value")
          output_file.write(f"Highest Value: {highest:.2f}\n")  # Format with 2 decimal places 
          output_file.write(f"Lowest Value: {lowest:.2f}\n")

          if missing_days:
            output_file.write("Missing Dates:\n")
            for date in missing_days:
              output_file.write(f"- {date.strftime('%Y-%m-%d')}\n")
          output_file.write("\n")  # Add a blank line between file summaries

        elif filename == "data_summary.txt":
          output_file.write("")
  
        else:
          output_file.write(f"Error processing file: {filename}\n\n")

if __name__ == "__main__":
  main()
