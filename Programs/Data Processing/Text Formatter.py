import os

# Define input and output directories
input_dir = r"C:\Users\thoma\Documents\GitHub\Drought-Research\Precip Data\Dataset B-a\Monthly Tot Unformatted"
output_dir = r"C:\Users\thoma\Documents\GitHub\Drought-Research\Precip Data\Dataset B-a\Monthly Tot Formatted"

# Loop through files in the input directory
for filename in os.listdir(input_dir):
    if filename.endswith(".txt"):  # Check for text files
        # Create full paths for input and output files
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)

        # Read data from the input file
        with open(input_path, "r") as f:
            data = f.readlines()[1:]

        # Process data as before
        with open(output_path, "a") as f:
            f.write("\n")
        lines = [line.strip() for line in data]
        for line in lines:
            year, month, average = line.split()
            year = int(year.strip())
            month = int(month.strip())
            average = float(average.strip())
            output_date = f"{month:02d}/{1:02d}/{year}"  # Replace 1 with the day (assuming it's not provided)

            # Write processed data to the output file
            with open(output_path, "a") as f:
                f.write(f"{output_date} {average}\n")

        print(f"Processed file: {filename}")

print("Completed processing all files in the input directory.")
