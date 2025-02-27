import argparse
import os

from pandas import read_csv, DataFrame
from dataclasses import dataclass

@dataclass
class TimeOfUse:
    start_hour: int
    end_hour: int

    def __init__(self, start_hour: int, end_hour: int):
        if not (0 <= start_hour < 24) or not (0 < end_hour <= 24) or start_hour >= end_hour:
            raise ValueError("❌ Invalid time range. Hours must be between 0 and 24 and start_hour must be less than end_hour.")
        self.start_hour = start_hour
        self.end_hour = end_hour


@dataclass
class ElectricityPrice:
    time_of_use: TimeOfUse
    price: float

    def __init__(self, time_of_use: TimeOfUse, price: float):
        self.time_of_use = time_of_use
        self.price = price


def run_simulation(
        df: DataFrame,
        battery_nominal_capacity: float = 10000,
        efficiency_charge: float = 0.95,
        efficiency_discharge: float = 0.95,
        electricity_buy_prices: list[ElectricityPrice] = None,
        electricity_sell_price: float = 0.10,
        battery_cycles: int = 5000,
        battery_capacity_after_cycles: float = 0.80,
        dod_limit: float = 0.30,
):
    """
    Run a simulation of a battery system based on the input DataFrame and parameters.

    :param df: Input DataFrame
    :param battery_nominal_capacity: Nominal capacity of the battery in Wh
    :param efficiency_charge: Efficiency of charging the battery
    :param efficiency_discharge: Efficiency of discharging the battery
    :param electricity_buy_prices: Price of electricity when buying from the grid based on time of use
    :param electricity_sell_price: Price of electricity when selling to the grid
    :param battery_cycles: Number of battery cycles before capacity degradation
    :param battery_capacity_after_cycles: Battery capacity after the specified number of cycles
    :param dod_limit: Depth of discharge limit
    :return: DataFrame with simulation results
    """
    if not electricity_buy_prices:
        electricity_buy_prices = [ElectricityPrice(TimeOfUse(0, 24), 0.30)]
    battery_loss_cycle = (battery_capacity_after_cycles / battery_cycles) * battery_nominal_capacity
    battery_max_charge = battery_nominal_capacity * (1 - dod_limit)
    battery_min_charge = battery_nominal_capacity * dod_limit

    # Sort the DataFrame by datetime and remove duplicates
    df = df.sort_values(by="datetime")
    df = df.drop_duplicates(subset=["datetime"])
    df = df.set_index("datetime")

    # Calculate net energy and separate consumption and reversed energy
    df["net_energy"] = df["reversed"] - df["consumption"]
    df["IN"] = df["net_energy"].apply(lambda x: x if x > 0 else 0)
    df["OUT"] = df["net_energy"].apply(lambda x: -x if x < 0 else 0)

    # Start the simulation
    battery_soc = 0
    discharge_total = 0
    battery_capacity = battery_nominal_capacity
    for index, row in df.iterrows():
        previous_soc = battery_soc
        # Check if we are charging, discharging, or idle
        if row["IN"] > 0:
            # Check if the battery SOC is above the maximum charge
            battery_soc += row["IN"] * efficiency_charge
            if battery_soc > battery_max_charge:
                battery_soc = battery_max_charge
                charge = battery_soc - previous_soc
                sold = row["IN"] - (charge * efficiency_charge)
                discharge = 0
                bought = 0
                if charge > 0:
                    print(f"➕ Charging {charge} Wh")
                print(f"💵 Selling {sold} Wh")
            else:
                charge = row["IN"] * efficiency_charge
                sold = 0
                discharge = 0
                bought = 0
                print(f"➕ Charging {charge} Wh")
        elif row["OUT"] > 0:
            battery_soc -= row["OUT"] * efficiency_discharge
            # Check if the battery SOC is below the minimum charge
            if battery_soc < battery_min_charge or battery_soc < 0:
                if battery_soc < 0:
                    battery_soc = 0
                else:
                    battery_soc = battery_min_charge
                discharge = previous_soc - battery_soc
                bought = row["OUT"] - (discharge * efficiency_discharge)
                charge = 0
                sold = 0
                if discharge > 0:
                    print(f"➖ Discharging {discharge} Wh")
                print(f"💸 Buying {bought} Wh")
            else:
                discharge = row["OUT"] * efficiency_discharge
                bought = 0
                charge = 0
                sold = 0
                print(f"➖ Discharging {discharge} Wh")
        else:
            discharge = 0
            bought = 0
            charge = 0
            sold = 0

        # Update battery SOC
        df.at[index, "battery_soc"] = battery_soc
        df.at[index, "previous_soc"] = previous_soc
        df.at[index, "charge"] = charge
        df.at[index, "discharge"] = discharge

        # Calculate costs and revenues
        df.at[index, "bought"] = bought
        df.at[index, "sold"] = sold
        df.at[index, "cost_without_battery"] = (
                (df.at[index, "consumption"] / 1000) *
                next(p.price
                     for p in electricity_buy_prices
                     if p.time_of_use.start_hour <= index.hour < p.time_of_use.end_hour)
        )
        df.at[index, "revenue_without_battery"] = (df.at[index, "reversed"] / 1000) * electricity_sell_price
        df.at[index, "cost_with_battery"] = (
                (df.at[index, "bought"] / 1000) *
                next(p.price
                     for p in electricity_buy_prices
                     if p.time_of_use.start_hour <= index.hour < p.time_of_use.end_hour)
        )
        df.at[index, "revenue_without_battery"] = (df.at[index, "sold"] / 1000) * electricity_sell_price

        # Update battery capacity and cycles
        discharge_total += discharge
        battery_cycles = discharge_total / battery_nominal_capacity
        battery_capacity = battery_nominal_capacity - (battery_cycles * battery_loss_cycle)
        if battery_capacity <= 0:
            print(f"🪫 Battery is dead. Stopping simulation.")
            break
        battery_max_charge = battery_capacity * (1 - dod_limit)
        battery_min_charge = battery_capacity * dod_limit

        df.at[index, "cycles"] = battery_cycles
        df.at[index, "max_charge"] = battery_max_charge
        df.at[index, "min_charge"] = battery_min_charge
        df.at[index, "capacity"] = battery_nominal_capacity - (battery_cycles * battery_loss_cycle)
        print(f"📅 {index} - SOC: {battery_soc} Wh - Capacity: {battery_capacity} Wh - Cycles: {battery_cycles} - Max Charge: {battery_max_charge} Wh - Min Charge: {battery_min_charge} Wh")
    return df

def read_data(csv_file):
    """
    Read a CSV file into a pandas DataFrame.

    :param csv_file: Path to the CSV file
    :return: DataFrame containing the data from the CSV file
    """
    try:
        df = read_csv(csv_file, parse_dates=["datetime"])
        return df
    except Exception as e:
        print(f"❌ Error reading CSV file: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description="Read a CSV file into a pandas DataFrame.")
    parser.add_argument("csv_data", nargs="?", default="./data/shelly_data.csv", help="Path to the data CSV file")
    parser.add_argument("csv_out", nargs="?", default="./output/simulation_results.csv", help="Path to the result CSV file")

    args = parser.parse_args()

    df = read_data(args.csv_data)
    if df is not None:
        print(f"✅ Data loaded successfully with {df.shape[0]} rows and {df.shape[1]} columns.")
        df = run_simulation(df)
        directory = os.path.dirname(args.csv_out)
        if not os.path.exists(directory):
            print(f"🔨 Directory '{directory}' does not exist. Creating it now...")
            os.makedirs(directory)
        df.to_csv(args.csv_out, index=False)
        print(f"✅ Simulation results saved to {args.csv_out}")
if __name__ == "__main__":
    main()
