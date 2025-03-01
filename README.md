# 📊 Shelly3EM Data

This project contains various scripts:
- `get_data.py`: Fetches energy consumption data from Shelly Control Cloud API and stores it in a CSV file.
- `generate_data.py`: Generates synthetic energy data for specified years and saves it to a CSV file.
- `battery_simulation.py`: Simulates battery usage based on energy data and saves the results to a CSV file.

## 🚀 Features

### Shelly3EM Data Fetching
- Fetches daily energy **consumption** and **reversed** data.
- Saves data to a CSV file.
- Skips dates that already exist in the CSV.
- Supports command-line arguments for flexibility.
- Automatically creates missing directories for the CSV file.

### Synthetic Data Generation
- Generates synthetic energy data for specified years.
- Supports some parameters for customizing consumption and production.
- Saves generated data to a CSV file.

### Battery Usage Simulation
- Simulates battery usage based on energy data.
- Calculates battery charge and discharge cycles.
- Supports custom battery capacity and efficiency.
- Supports calculation of costs.
- Supports custom time of use prices.
- Supports calculation of revenue.
- Saves simulation results to a CSV file.

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

### Fetch Data
```bash
pdm run get_data --start_date YYYY-MM-DD --end_date YYYY-MM-DD --out /path/to/data.csv
```

### Generate Synthetic Data
```bash
pdm run generate_data --out /path/to/generated_data.csv --start_year 2025 --years 1
```

### Simulate Battery Usage
```bash
pdm run battery_simulation --csv_data /path/to/data.csv --csv_out /path/to/simulation_results.csv
```

### ✅ Example

#### Fetch Data
```bash
pdm run get_data --start_date 2023-09-29 --end_date 2025-02-24 --out ./data.csv
```

#### Generate Synthetic Data
```bash
pdm run generate_data --out ./generated_data.csv --start_year 2025 --years 1
```

#### Simulate Battery Usage
```bash
pdm run battery_simulation --csv_data ./data.csv --csv_out ./simulation_results.csv
```

## 📂 CSV File Format

### Data Fetching
The `get_data` script appends data to a CSV file with the following format:

| datetime            | consumption | reversed |
|---------------------|-------------|----------|
| 2025-09-30 00:00:00 | 120.5       | 10.3     |
| 2025-10-01 00:00:00 | 135.2       | 12.1     |

- `datetime`: Timestamp of the data entry.
- `consumption`: Energy registered in input from the Shelly in **watt-hours (Wh)**.
- `reversed`: Energy registered in output from the Shelly in **watt-hours (Wh)**.

### Synthetic Data Generation
The `generate_data` script creates a CSV file with the following format:

| datetime            | Energy_Consumed_Wh | Energy_Produced_Wh | consumption | reversed |
|---------------------|--------------------|--------------------|-------------|----------|
| 2025-01-01 00:00:00 | 150.0              | 50.0               | 105.0       | 5.0      |
| 2025-01-01 01:00:00 | 160.0              | 55.0               | 110.5       | 5.5      |
| 2025-01-01 02:00:00 | 170.0              | 60.0               | 104.0       | 6.0      |

- `datetime`: Timestamp of the data entry.
- `Energy_Consumed_Wh`: Energy consumed in **watt-hours (Wh)**.
- `Energy_Produced_Wh`: Energy produced in **watt-hours (Wh)**.
- `consumption`: Energy taken from the grid in **watt-hours (Wh)**.
- `reversed`: Energy returned to the grid in **watt-hours (Wh)**.

### Battery Usage Simulation
The `battery_simulation` script creates a CSV file with the following format:

| datetime            | consumption | reversed | previous\_soc | battery\_soc | charge | discharge | bought     | sold | cost\_without\_battery | revenue\_without\_battery | cost\_with\_battery | revenue\_with\_battery | cycles              | max\_charge     | min\_charge       | capacity       |
|---------------------|-------------|----------|---------------|--------------|--------|-----------|------------|------|------------------------|---------------------------|---------------------|------------------------|---------------------|-----------------|-------------------|----------------|
| 2023-09-30 12:00:00 | 0.0         | 0.0      | 675.0         | 675.0        | 0.0    | 0.0       | 0.0        | 0.0  | 0.0                    | 0.0                       | 0.0                 | 0.0                    | 0.0                 | 12825.0         | 675.0             | 13500.0        |
| 2023-09-30 13:00:00 | 0.0         | 0.0      | 675.0         | 675.0        | 0.0    | 0.0       | 0.0        | 0.0  | 0.0                    | 0.0                       | 0.0                 | 0.0                    | 0.0                 | 12825.0         | 675.0             | 13500.0        |
| 2023-09-30 14:00:00 | 0.0         | 0.0      | 675.0         | 675.0        | 0.0    | 0.0       | 0.0        | 0.0  | 0.0                    | 0.0                       | 0.0                 | 0.0                    | 0.0                 | 12825.0         | 675.0             | 13500.0        |
| 2023-09-30 15:00:00 | 1818.75     | 1474.29  | 675.0         | 675.0        | 1401.0 | 1400.5755 | 488.203275 | 0.0  | 0.5280889762500001     | 0.147429                  | 0.141753824163105   | 0.0                    | 0.10374633333333333 | 12824.787112524 | 674.9887953960001 | 13499.77590792 |

- `datetime`: Timestamp of the data entry.
- `consumption`: Energy taken from the grid in **watt-hours (Wh)**.
- `reversed`: Energy returned to the grid in **watt-hours (Wh)**.
- `previous_soc`: Previous state of charge of the battery in **watt-hours (Wh)**.
- `battery_soc`: Current state of charge of the battery in **watt-hours (Wh)**.
- `charge`: Energy stored in the battery in **watt-hours (Wh)**.
- `discharge`: Energy taken from the battery in **watt-hours (Wh)**.
- `bought`: Energy bought from the grid in **watt-hours (Wh)**.
- `sold`: Energy sold to the grid in **watt-hours (Wh)**.
- `cost_without_battery`: Cost without battery in **currency**.
- `revenue_without_battery`: Revenue without battery in **currency**.
- `cost_with_battery`: Cost with battery in **currency**.
- `revenue_with_battery`: Revenue with battery in **currency**.
- `cycles`: Number of charge and discharge cycles.
- `max_charge`: Maximum charge of the battery in **watt-hours (Wh)**.
- `min_charge`: Minimum charge of the battery in **watt-hours (Wh)**.
- `capacity`: Capacity of the battery in **watt-hours (Wh)**.

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
