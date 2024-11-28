from json_configuration_reader import *
from investment_strategy import *
import matplotlib.pyplot as plt
import datetime as dt
from simulator import *
import csv

INITIAL_INVESTMENT = 100
LOG_FILE = "../execution_logs/PEPEUSDT-250.csv"
COIN_NAME = "PEPEUSDT"
CURRENCY_NAME = "PEPE"
BASE_CURRENCY_NAME = "USDT"
AVG_HRS = 1
SHORT_AVG_HRS = 1
LONG_AVG_HRS = 3
BUY_TAX = 0.1
SELL_TAX = 0.1
MIN_DELTA = 3.5
STOP_LOSS = 25
SLEEP_DAYS_AFTER_LOSS = 0
MAX_INVESTMENT = 100000


def read_log_file(path: str) -> tuple[list, list]:
    # Read the CSV log file
    log_location = Path(__file__).absolute().parent
    file_location = log_location / path

    # Verify the log file presence
    if not os.path.exists(file_location):
        raise Exception("[ERR] The log file does not exist")

    # Open the file
    file = file_location.open()
    reader = csv.DictReader(file)

    # Read the content
    data_ts = []
    data_price = []
    data_unix = []
    for row in reader:
        data_ts.append(int(row["timestamp"]))
        data_price.append(float(row["current_price"]))
        data_unix.append(dt.datetime.fromtimestamp(int(row["timestamp"])))

    file.close()
    return (data_ts, data_unix, data_price)


def main():
    # Create user configuration
    config = UserConfiguration()
    config.ALGORITHM_TYPE = AlgorithmType.CROSSOVER
    config.AVG_HRS = AVG_HRS
    config.SHORT_AVG_HRS = SHORT_AVG_HRS
    config.LONG_AVG_HRS = LONG_AVG_HRS
    config.COIN_NAME = COIN_NAME
    config.CURRENCY_NAME = CURRENCY_NAME
    config.BASE_CURRENCY_NAME = BASE_CURRENCY_NAME
    config.BUY_TAX = BUY_TAX
    config.SELL_TAX = SELL_TAX
    config.STOP_LOSS = STOP_LOSS
    config.SLEEP_DAYS_AFTER_LOSS = SLEEP_DAYS_AFTER_LOSS
    config.MIN_DELTA = MIN_DELTA

    # Check config consistence
    if config.SHORT_AVG_HRS > config.LONG_AVG_HRS:
        print("[ERR] Long average is less than small average")
        return

    # Gather the data
    (data_ts, data_date, data_price) = read_log_file(LOG_FILE)

    # Create plots
    fig, ax = plt.subplots()

    # Simulate the event with the simulator class
    simulation_result = simulate(config, data_ts, data_price)

    # Retrieve the simulation objects
    avg_time = [dt.datetime.fromtimestamp(
        sim_step.timestamp) for sim_step in simulation_result]
    avg_price = [sim_step.considered_avg for sim_step in simulation_result]
    avg_short_price = [
        sim_step.considered_short_avg for sim_step in simulation_result]
    avg_long_price = [
        sim_step.considered_long_avg for sim_step in simulation_result]

    # Evaluate all the actions
    prev_action = Action.NONE
    for sim_step in simulation_result:
        date_timestamp = dt.datetime.fromtimestamp(sim_step.timestamp)
        # Buy action
        if sim_step.last_action != prev_action and sim_step.last_action == Action.BUY:
            ax.axvline(date_timestamp, color="b", label="BUY")

            # Report the buy action
            print(
                f"[{date_timestamp}]BUY \t {config.BASE_CURRENCY_NAME}:\t" +
                f"{sim_step.current_base_coin_availability: .2f}\t{config.CURRENCY_NAME}:\t{sim_step.current_coin_availability:.8f}")
        # Sell action
        elif sim_step.last_action != prev_action and (sim_step.last_action == Action.SELL or sim_step.last_action == Action.SELL_LOSS):
            ax.axvline(date_timestamp, color="g", label="SELL")

            # Report the sell action
            print(
                f"[{date_timestamp}]SELL \t {config.BASE_CURRENCY_NAME}:\t" +
                f"{sim_step.current_base_coin_availability:.2f}\t{config.CURRENCY_NAME}:\t{sim_step.current_coin_availability:.8f}")

        # Update the previous action
        prev_action = sim_step.last_action

    # Plot also the average considered price
    ax.plot(data_date, data_price)
    ax.plot(avg_time, avg_price, color="yellow")
    ax.plot(avg_time, avg_short_price, color="red")
    ax.plot(avg_time, avg_long_price, color="orange")

    plt.show()


if __name__ == "__main__":
    main()
