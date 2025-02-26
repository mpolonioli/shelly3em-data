import argparse
import os

from pandas import read_csv, DataFrame

def run_simulation(
        df: DataFrame,
        battery_capacity: float = 10000,
        efficiency_charge: float = 0.95,
        efficiency_discharge: float = 0.95,
        electricity_buy_price: float = 0.30,
        electricity_sell_price: float = 0.10,
        battery_cycles: int = 5000,
        battery_capacity_after_cycles: float = 0.80,
        dod_limit: float = 0.30,
):
    """
    Run a simulation of a battery system based on the input DataFrame and parameters.

    :param df: Input DataFrame
    :param battery_capacity: Battery capacity in Wh
    :param efficiency_charge: Efficiency of charging the battery
    :param efficiency_discharge: Efficiency of discharging the battery
    :param electricity_buy_price: Price of electricity when buying from the grid
    :param electricity_sell_price: Price of electricity when selling to the grid
    :param battery_cycles: Number of battery cycles before capacity degradation
    :param battery_capacity_after_cycles: Battery capacity after the specified number of cycles
    :param dod_limit: Depth of discharge limit
    :return: DataFrame with simulation results
    """
    battery_loss_cycle = (battery_capacity_after_cycles / battery_cycles) * battery_capacity
    battery_max_charge = battery_capacity * (1 - dod_limit)
    battery_min_charge = battery_capacity * dod_limit
    df = df.sort_values(by="datetime")
    df = df.drop_duplicates(subset=["datetime"])
    df = df.set_index("datetime")
    df["net_energy"] = df["reversed"] - df["consumption"]
    df["IN"] = df["net_energy"].apply(lambda x: x if x > 0 else 0)
    df["OUT"] = df["net_energy"].apply(lambda x: -x if x < 0 else 0)
    battery_soc = 0
    battery_actual_capacity = battery_max_charge
    discharge_total = 0
    for index, row in df.iterrows():
        previous_soc = battery_soc
        if row["IN"] > 0:
            charge = row["IN"] * efficiency_charge
            battery_soc += charge
            if battery_soc > battery_actual_capacity:
                battery_soc = battery_actual_capacity
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
        df.at[index, "battery_soc"] = battery_soc
        df.at[index, "previous_soc"] = previous_soc
        df.at[index, "charge"] = charge
        df.at[index, "discharge"] = discharge
        df.at[index, "bought"] = bought
        df.at[index, "sold"] = sold
        print(f"📅 {index} - SOC: {battery_soc} Wh")

        discharge_total += discharge
        battery_cycles = discharge_total / battery_capacity
        battery_actual_capacity = battery_max_charge - (battery_cycles * battery_loss_cycle)
        if battery_actual_capacity < battery_min_charge:
            battery_min_charge = battery_actual_capacity
        df.at[index, "cycles"] = battery_cycles
        df.at[index, "capacity"] = battery_actual_capacity
    df["cost_without_battery"] = (df["consumption"] / 1000) * electricity_buy_price
    df["revenue_without_battery"] = (df["reversed"] / 1000) * electricity_sell_price
    df["cost_with_battery"] = (df["bought"] / 1000) * electricity_buy_price
    df["revenue_with_battery"] = (df["sold"] / 1000) * electricity_sell_price
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
