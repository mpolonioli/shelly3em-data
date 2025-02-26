# 📊 Shelly3EM Data

This script fetches energy consumption data from Shelly Control Cloud API and stores it in a CSV file. It ensures no duplicate entries by checking the existing CSV file before making API requests.

## 🚀 Features

- Fetches daily energy **consumption** and **reversed** data.
- Saves data to a CSV file.
- Skips dates that already exist in the CSV.
- Supports command-line arguments for flexibility.
- Automatically creates missing directories for the CSV file.

## 📦 Installation

1. Install required dependencies:
   ```bash
   pdm install
   ```
2. Create a `.env` file in the project folder and add:
   ```ini
   SHELLY_AUTH_KEY=shelly_auth_key_here
   SHELLY_URL=shelly_api_url_here
   SHELLY_ID=shelly3em_id_here
   ```

The `SHELLY_AUTH_KEY` and the `SHELLY_URL` variables are the same used in the [Shelly Control Cloud API](https://shelly-api-docs.shelly.cloud/cloud-control-api/).

## 🔧 Usage
```bash
pdm start --start_date YYYY-MM-DD --end_date YYYY-MM-DD --csv_file /path/to/data.csv
```

### ✅ Example

```bash
pdm start --start_date 2023-09-29 --end_date 2025-02-24 --csv_file ./data.csv
```

- ``: (Required) The starting date (YYYY-MM-DD).
- ``: (Optional) The ending date (YYYY-MM-DD). Default is today.
- ``: (Optional) Path to the CSV file. Default is `./data.csv`.

## 📂 CSV File Format

The script appends data to a CSV file with the following format:

| datetime            | consumption | reversed |
|---------------------|-------------|----------|
| 2025-09-30 00:00:00 | 120.5       | 10.3     |
| 2025-10-01 00:00:00 | 135.2       | 12.1     |

- ``: Timestamp of the data entry.
- ``: Energy consumed in **watt-hours (Wh)**.
- ``: Energy returned to the grid in **watt-hours (Wh)**.

## 🛠 Error Handling

- If the **CSV file is not writable**, an error is displayed.
- If the **date format is incorrect**, the script will exit with an error.
- If the **API request fails**, it logs the error message and continues.
- If the **response format is unexpected**, a warning is displayed.

## 📝 Notes

- Ensure your Shelly auth key and URL is **valid**.
- The script automatically creates the **CSV file and directories** if they don't exist.
- The script **skips duplicate dates** to avoid redundant API calls.

## 📜 License

This project is licensed under the MIT License.

## 📩 Contact

For any issues or suggestions, feel free to open an issue or contribute! 😊

