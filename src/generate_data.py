import argparse
import asyncio
import os
import time

import numpy as np
import pandas as pd
from src.utils import is_valid_path

# Seasonal adjustment function
def seasonal_adjustment(month, cold_months, hot_months, cold_factor, hot_factor):
    if month in cold_months:
        return cold_factor
    elif month in hot_months:
        return hot_factor
    else:
        return 1.0

# Determine daylight hours based on the month
def get_daylight_hours(month, cold_months, hot_months, cold_range, hot_range):
    if month in cold_months:
        return cold_range
    elif month in hot_months:
        return hot_range
    else:
        return round((cold_range[0] + hot_range[0]) / 2), round((cold_range[1] + hot_range[1]) / 2)

# Determine solar production range based on the month
def get_production_range(month, cold_months, hot_months, cold_range, hot_range):
    if month in cold_months:
        return cold_range
    elif month in hot_months:
        return hot_range
    else:
        return round((cold_range[0] + hot_range[0]) / 2), round((cold_range[1] + hot_range[1]) / 2)

# Energy consumption model
async def generate_consumption(hour, month, base_range, peak_range, cold_months, hot_months, cold_factor, hot_factor):
    if 6 <= hour < 9 or 17 <= hour < 22:  # Peak hours
        peak = np.random.uniform(*peak_range)
    else:
        peak = np.random.uniform(*base_range)
    return round(peak * seasonal_adjustment(month, cold_months, hot_months, cold_factor, hot_factor))

# Solar energy production model with variable daylight hours and seasonal ranges
async def generate_production(hour, month, cold_months, hot_months, cold_daylight_range, hot_daylight_range, cold_production_range, hot_production_range):
    daylight_start, daylight_end = get_daylight_hours(month, cold_months, hot_months, cold_daylight_range, hot_daylight_range)
    production_min, production_max = get_production_range(month, cold_months, hot_months, cold_production_range, hot_production_range)

    if daylight_start <= hour < daylight_end:
        peak = np.sin((hour - daylight_start) / (daylight_end - daylight_start) * np.pi) * np.random.uniform(production_min, production_max)
        return round(peak)
    return 0

# Function to calculate energy taken from and returned to the grid
def calculate_grid_usage(consumed, produced, self_consumption_ratio):
    used_from_production = min(consumed, produced * self_consumption_ratio)
    net_consumed = consumed - used_from_production
    net_produced = produced - used_from_production

    taken_from_grid = max(0, net_consumed)
    returned_to_grid = max(0, net_produced)

    return taken_from_grid, returned_to_grid

# Async function to generate data for a single year
async def generate_yearly_data(year, base_range, peak_range, cold_months, hot_months, cold_factor, hot_factor, self_consumption_ratio, cold_daylight_range, hot_daylight_range, cold_production_range, hot_production_range):
    hours = pd.date_range(start=f"{year}-01-01", end=f"{year}-12-31 23:00", freq='h')

    generate_consumption_tasks = [generate_consumption(h.hour, h.month, base_range, peak_range, cold_months, hot_months, cold_factor, hot_factor) for h in hours]
    generate_production_tasks = [generate_production(h.hour, h.month, cold_months, hot_months, cold_daylight_range, hot_daylight_range, cold_production_range, hot_production_range) for h in hours]
    consumed, produced = await asyncio.gather(
        asyncio.gather(*generate_consumption_tasks),
        asyncio.gather(*generate_production_tasks)
    )

    grid_usage = [calculate_grid_usage(c, p, self_consumption_ratio) for c, p in zip(consumed, produced)]
    taken_from_grid, returned_to_grid = zip(*grid_usage)

    return pd.DataFrame({
        "datetime": hours,
        "Energy_Consumed_Wh": consumed,
        "Energy_Produced_Wh": produced,
        "consumed": taken_from_grid,
        "reversed": returned_to_grid,
    })

# Generate energy dataset
async def generate_energy_data(start_year, years, base_range, peak_range, cold_months, hot_months, cold_factor, hot_factor, self_consumption_ratio, cold_daylight_range, hot_daylight_range, cold_production_range, hot_production_range):
    tasks = [
        generate_yearly_data(year, base_range, peak_range, cold_months, hot_months, cold_factor, hot_factor, self_consumption_ratio, cold_daylight_range, hot_daylight_range, cold_production_range, hot_production_range)
        for year in range(start_year, start_year + years)
    ]
    return pd.concat(await asyncio.gather(*tasks), ignore_index=True)

# Main function with argparse
async def main():
    parser = argparse.ArgumentParser(description="Generate energy dataset with seasonal solar production and self-consumption.")

    parser.add_argument("--out", type=str, default="./data/generated_data.csv", help="Path to the CSV file (default: ./data/generated_data.csv)")

    parser.add_argument("--start_year", type=int, default=2025, help="Starting year.")
    parser.add_argument("--years", type=int, default=1, help="Number of years.")

    parser.add_argument("--base_range", type=float, nargs=2, default=(500, 1500), help="Base consumption range (Wh).")
    parser.add_argument("--peak_range", type=float, nargs=2, default=(2000, 4500), help="Peak consumption range (Wh).")
    parser.add_argument("--cold_months", type=int, nargs="+", default=[12, 1, 2], help="Cold months.")
    parser.add_argument("--hot_months", type=int, nargs="+", default=[6, 7, 8], help="Hot months.")
    parser.add_argument("--cold_factor", type=float, default=1.3, help="Multiplier for cold months.")
    parser.add_argument("--hot_factor", type=float, default=1.2, help="Multiplier for hot months.")

    parser.add_argument("--self_consumption_ratio", type=float, default=0.7, help="Percentage of produced energy used for consumption (0-1).")
    parser.add_argument("--cold_daylight_range", type=int, nargs=2, default=(8, 16), help="Cold months daylight range: start_hour, end_hour.")
    parser.add_argument("--hot_daylight_range", type=int, nargs=2, default=(6, 20), help="Hot months daylight range: start_hour, end_hour.")
    parser.add_argument("--cold_production_range", type=int, nargs=2, default=(1000, 3000), help="Cold months production range (Wh).")
    parser.add_argument("--hot_production_range", type=int, nargs=2, default=(3000, 6000), help="Hot months production range (Wh).")

    args = parser.parse_args()

    if not is_valid_path(args.out):
        return

    print("🔋 Generating energy data...")
    start_time = time.time()
    df = await generate_energy_data(args.start_year, args.years, args.base_range, args.peak_range, args.cold_months, args.hot_months, args.cold_factor, args.hot_factor, args.self_consumption_ratio, args.cold_daylight_range, args.hot_daylight_range, args.cold_production_range, args.hot_production_range)
    print(f"⏱️ Generation completed in {time.time() - start_time:.2f} seconds")

    df.to_csv(args.out, index=False)
    print(f"✅ Generation data saved to '{args.out}'")

    args_file = os.path.join(os.path.dirname(args.out), "generation_args.txt")
    with open(args_file, "w") as f:
        print("🔧 Generation parameters:")
        for arg, value in vars(args).items():
            print(f"\t- {arg}: {value}")
            f.write(f"{arg}: {value}\n")
    print(f"✅ Generation parameters saved to {args_file}")

if __name__ == "__main__":
    asyncio.run(main())
