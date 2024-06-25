import os
from datetime import date, timedelta

def calculate_quality_control(filename):
  """
  This function quality controls data from a text file.

  Args:
    filename: The name of the text file.

  Returns:
    A tuple containing two tuples: (first_month, first_day, first_year), (last_month, last_day, last_year)
  """

  missing_days = []
  previous_date = None
  first_month, first_day, first_year = None, None, None
  last_month, last_day, last_year = None, None, None

  quality_control_data = {}
  with open(filename, "r") as f:
    line_count = 0
    for line in f:
      if line_count >= 3:
        month, day, year, data = line.strip().split()
        data = float(data)

        # Initialize or add to monthly data
      if first_month is None or (year, month, day) < (first_year, first_month, first_day):
        first_month, first_day, first_year = month, day, year
      if last_month is None or (year, month, day) > (last_year, last_month, last_day):
        last_month, last_day, last_year = month, day, year
      if previous_date is not None:
        # Handle cases where month or year changes
        if current_date.month != previous_date.month or current_date.year != previous_date.year:
          # Use a loop to fill missing dates considering month transitions
          missing_days.extend(get_missing_dates_with_months(previous_date, current_date))
        else:
          # Handle simple case within the same month
          missing_dates.extend(get_missing_dates(previous_date, current_date))

      previous_date = current_date

  return (first_month, first_day, first_year), (last_month, last_day, last_year), missing_days

def process_folder(folder_path):
  """
  Processes all files in a folder and quality controls data.

  Args:
    folder_path: The path to the folder containing text files.
  """
  for filename in os.listdir(folder_path):
    file_path = os.path.join(folder_path, filename)
    if os.path.isfile(file_path):
      # Quality Control the Data
      monthly_totals_data = calculate_quality_control(file_path)

      # Create and write output file
      output_filename = os.path.splitext(filename)[0] + "_QC_Results.txt"
      output_path = os.path.join(folder_path, output_filename)
      with open(output_path, "w") as f:
        f.write("Quality Control Findings\n")
        for month, total in monthly_totals_data.items():
          f.write(f"{month}{total:.4f}\n")

      print(f"Finished processing: {file_path}")
      
def get_missing_dates_with_months(start_date, end_date):
  """
  This helper function generates a list of missing dates between two dates
  (inclusive) considering month transitions and potential year changes.

  Args:
      start_date: The starting date (datetime.date object).
      end_date: The ending date (datetime.date object).

  Returns:
      A list of missing dates (datetime.date objects) between start and end date.
  """

  missing_dates = []
  current_date = start_date

  while current_date < end_date:
    # Check if dates are within the same month
    if current_date.month == end_date.month and current_date.year == end_date.year:
      # Use simpler logic for dates within the same month (already handled in get_missing_dates)
      missing_dates.extend(get_missing_dates(current_date, end_date))
      break  # Exit loop as remaining dates are handled within the same month

    # Handle case where month changes but year remains the same
    if current_date.year == end_date.year:
      # Move to the end of the current month using the calendar module
      next_month = current_date.month + 1
      next_date = current_date.replace(month=next_month, day=1)  # Move to next month's 1st
      # Adjust for number of days in the next month
      last_day_of_next_month = next_date.replace(day=28)  # Start with 28 (common case)
      while last_day_of_next_month < next_date:  # Loop until we find the last day
        last_day_of_next_month = last_day_of_next_month.replace(day=last_day_of_next_month.day + 1)
      # Add missing days until the end of the current month
      missing_dates.extend(get_missing_dates(current_date, last_day_of_next_month - timedelta(days=1)))
      current_date = next_date  # Move to next month's 1st for next iteration


def get_missing_dates(start_date, end_date):
  """
  This helper function generates a list of missing dates between two dates
  (inclusive) assuming chronological order within the same month.

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

# Modify the path to the folder you want to read
folder_path = r"C:\Users\tpsqmd\Desktop\Daily"
process_folder(folder_path)