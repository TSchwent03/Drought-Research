import os
from itertools import islice

def calculate_monthly_totals(filename):
    """
    This function calculates monthly totals from a text file.

    Args:
        filename: The name of the text file.

    Returns:
        A dictionary where keys are months and values are lists of daily totals.
    """
    monthly_data = {}
    with open(filename, "r") as f:
        line_count = 0
        for line in f:
            if line_count >= 3:
                month, day, year, data = line.strip().split()
                data = float(data)

                month_key = f"{year:10}{month:10}"

                # Initialize or add to monthly data
                if month_key not in monthly_data:
                    monthly_data[month_key] = []
                monthly_data[month_key].append(data)
            line_count += 1

    # Calculate monthly averages
    for month, daily_data in monthly_data.items():
        monthly_data[month] = sum(daily_data)

    return monthly_data

def process_folder(folder_path):
    """
    Processes all files in a folder and calculates monthly totals.

    Args:
        folder_path: The path to the folder containing text files.
    """
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        if os.path.isfile(file_path):
            # Calculate monthly averages
            monthly_totals_data = calculate_monthly_totals(file_path)

            # Create and write output file (CSV)
            output_filename = os.path.splitext(filename)[0] + "_totals.csv"
            output_path = os.path.join(folder_path, output_filename)

            with open(output_path, "w") as f:
                f.write("Year,Month,Total\n")  # Write header
                for month, total in monthly_totals_data.items():
                    year = month[:10]
                    month = month[10:]
                    f.write(f"{year},{month},{total:.4f}\n")

            print(f"Finished processing: {file_path}")

# Modify the path to the folder you want to read
folder_path = r"C:\Users\thoma\Documents\GitHub\Drought-Research\Precip Data\Dataset B-a\Daily Raw"
process_folder(folder_path)