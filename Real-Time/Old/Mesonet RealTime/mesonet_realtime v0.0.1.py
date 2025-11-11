import requests
from bs4 import BeautifulSoup
import datetime
import calendar

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
            for line in data_text.split("\n"):
                if "Total" in line:
                    total_line = line
                    break
            if total_line:
                total_precipitation = total_line.split()[-1]
                results.append(f"{station_name} ({station_code}): {total_precipitation}")
    return results

# Get current date
now = datetime.datetime.now()

# Define periods
periods = [
    ("Past Month", 1),
    ("Past 3 Months", 3),
    ("Past 6 Months", 6),
    ("Past 12 Months", 12),
]

# Fetch and print data for each period
for period_name, months_ago in periods:
    print(f"\n{period_name}:")

    # Determine start and end dates based on current day and months ago
    if now.day > 7:
        start_month = (now.month - months_ago) % 12  # months_ago months ago
        if start_month == 0:
          start_month = 12
        end_month = (now.month - 1) % 12
        if end_month == 0:
          end_month = 12
        if start_month > end_month:
          start_year = now.year - (start_month == 0) - 1  # Adjust year if December
        else:
          start_year = now.year - (start_month == 0)  # Adjust year if December
        end_year = now.year - (end_month == 0)  # Adjust year if December
    else:
        start_month = (now.month - months_ago - 1) % 12  # months_ago months ago
        if start_month == 0:
          start_month = 12
        end_month = (now.month - 2) % 12
        if end_month == 0:
          end_month = 12
        if start_month > end_month:
          start_year = now.year - (start_month == 0) - 1  # Adjust year if December
        else:
          start_year = now.year - (start_month == 0)  # Adjust year if December
        end_year = now.year - (end_month == 0)

    start_day = 1
    _, end_day = calendar.monthrange(end_year, end_month)

    print(f"Start Date: {start_month}, {start_day}, {start_year}")
    print(f"End Date: {end_month}, {end_day}, {end_year}")

    # Call fetch_data with calculated date parameters
    results = fetch_data(start_month, end_month, start_day, end_day, start_year, end_year)
    for result in results:
        print(result)