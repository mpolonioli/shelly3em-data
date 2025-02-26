import csv
import datetime
import os
import argparse
import requests
from dotenv import load_dotenv

# Load env
load_dotenv()
shelly_auth_key = os.getenv("SHELLY_AUTH_KEY")
shelly_id = os.getenv("SHELLY_ID")
shelly_url = os.getenv("SHELLY_URL")

if not shelly_auth_key:
    raise ValueError("❌ Error: missing property SHELLY_AUTH_KEY in .env file")
if not shelly_id:
    raise ValueError("❌ Error: missing property SHELLY_ID in .env file")
if not shelly_url:
    raise ValueError("❌ Error: missing property SHELLY_URL in .env file")

url = f"https://{shelly_url}/v2/statistics/power-consumption/em-3p"

def get_data(start_date, end_date, csv_file):
    """
    Retrieves data from the API for the specified date range and saves it to a CSV file.

    :param start_date: Start date (datetime.date)
    :param end_date: End date (datetime.date)
    :param csv_file: Path to the CSV file
    """

    # Set up headers with authorization
    headers = {
        "Accept": "application/json"
    }

    # Load existing datetime values from the CSV file to avoid duplicates
    existing_dates = set()
    if os.path.exists(csv_file):
        with open(csv_file, mode="r", newline="") as file:
            reader = csv.reader(file)
            next(reader, None)  # Skip header row
            for row in reader:
                if row:  # Ensure row is not empty
                    existing_dates.add(row[0])  # Assuming 'datetime' is in the first column

    # Open CSV file in append mode
    with open(csv_file, mode="a", newline="") as file:
        writer = csv.writer(file)

        # Write the header if the file is empty or new
        if os.path.getsize(csv_file) == 0:
            writer.writerow(["datetime", "consumption", "reversed"])

        # Loop through each day in the range
        current_date = start_date
        while current_date <= end_date:

            # Format date in the required format
            day = current_date.strftime("%Y-%m-%d")
            first_hour = current_date.strftime("%Y-%m-%d 00:00:00")
            last_hour = (current_date + datetime.timedelta(hours=23)).strftime("%Y-%m-%d 23:00:00")

            # Move to the next day
            current_date += datetime.timedelta(days=1)

            # Skip request if the datetime already exists in the CSV file
            if first_hour in existing_dates and last_hour in existing_dates:
                print(f"➡️ Skipping {day}, already in CSV.")
                continue

            # Set query parameters
            params = {
                "date_from": first_hour,
                "date_range": "day",
                "channel": 0,
                "id": shelly_id,
                "auth_key": shelly_auth_key,
            }

            # Make the GET request
            response = requests.get(url, headers=headers, params=params)

            # Check if the request was successful
            if response.status_code == 200:
                body = response.json()
                data = body["sum"]

                # Ensure response contains the expected properties
                if isinstance(data, list):  # Assuming the API returns a list of records
                    for entry in data:
                        datetime_value = entry.get("datetime", "N/A")
                        if entry.get("missing"):
                            print(f"➡️ Skipping {datetime_value}, missing data.")
                            continue
                        consumption_value = entry.get("consumption", "N/A")
                        reversed_value = entry.get("reversed", "N/A")

                        # Append to CSV
                        if datetime_value not in existing_dates:
                            writer.writerow([datetime_value, consumption_value, reversed_value])
                            print(f"➕ Appended: {datetime_value}, {consumption_value}, {reversed_value}")
                        else:
                            print(f"➡️ Skipping {datetime_value}, already in CSV.")
                else:
                    print(f"⚠️ Unexpected response format for {day}: {body}")
            else:
                print(f"⚠️ Error for {day}: {response.status_code}, {response.text}")

    print(f"\n✅ Data collection complete. Saved to {csv_file}")

def is_valid_path(csv_file):
    """
    Checks if the CSV file path is valid. Verifies that the directory exists and the file is writable.

    :param csv_file: Path to the CSV file
    :return: True if the path is valid, False otherwise
    """
    directory = os.path.dirname(csv_file)

    # Create the directory if it doesn't exist
    if not os.path.exists(directory):
        print(f"🔨 Directory '{directory}' does not exist. Creating it now...")
        os.makedirs(directory)

    # Check if the file is writable
    try:
        with open(csv_file, "a"):
            pass
        return True
    except IOError:
        print(f"❌ Error: The file '{csv_file}' is not writable.")
        return False

def main():
    """
    Main function to handle command-line arguments and start data collection.
    """
    # Argument parser for command-line options
    parser = argparse.ArgumentParser(description="Fetch data from an API and save it to a CSV file.")
    parser.add_argument("--start_date", type=str, required=True, help="Start date in YYYY-MM-DD format")
    parser.add_argument("--end_date", type=str, default=datetime.datetime.now().strftime("%Y-%m-%d"), help="End date in YYYY-MM-DD format (default: today)")
    parser.add_argument("--out", type=str, default="./data/shelly_data.csv", help="Path to the CSV file (default: ./data/shelly_data.csv)")

    args = parser.parse_args()

    # Convert string dates to datetime.date objects
    try:
        start_date = datetime.datetime.strptime(args.start_date, "%Y-%m-%d").date()
        end_date = datetime.datetime.strptime(args.end_date, "%Y-%m-%d").date()
    except ValueError:
        print("❌ Error: Invalid date format. Use YYYY-MM-DD.")
        return

    # Check that start_date is not later than end_date
    if start_date > end_date:
        print("❌ Error: start_date must be earlier than or equal to end_date.")
        return

    # Validate CSV file path
    if not is_valid_path(args.out):
        return

    # Call the get_data function with the provided arguments
    get_data(start_date, end_date, args.out)

# Run the main function if the script is executed directly
if __name__ == "__main__":
    main()
