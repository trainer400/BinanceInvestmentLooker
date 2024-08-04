from json_configuration_reader import *
from investment_strategy import *
import matplotlib.pyplot as plt
import datetime as dt
import time
import csv

INITIAL_INVESTMENT = 100
LOG_FILE = "../execution_logs/PEPEUSDT-300.csv"
COIN_NAME = "PEPEUSDT"
CURRENCY_NAME = "PEPE"
BASE_CURRENCY_NAME = "USDT"
AVG_HRS = 1
SHORT_AVG_HRS = 291
LONG_AVG_HRS = 301
BUY_TAX = 0.1
SELL_TAX = 0.1
MIN_DELTA = 3.5
STOP_LOSS = 10
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


def compute_avg_price(data_ts: list, data_price: list, avg_hrs: int, starting_timestamp: int):
    # Delta in seconds that the requested average impacts on the timestamp
    delta_seconds = avg_hrs * 60 * 60

    # Sum all the prices that correspond to a timestamp that is inside the considered average window
    result = 0
    counter = 0
    for i in range(len(data_ts)):
        if data_ts[i] < starting_timestamp and data_ts[i] > starting_timestamp - delta_seconds:
            result += data_price[i]
            counter += 1
        elif data_ts[i] > starting_timestamp:
            break
    return float(result) / counter


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

    if config.SHORT_AVG_HRS > config.LONG_AVG_HRS:
        print("[ERR] Long average is less than small average")
        return

    # Create an internal state to use during the simulation
    state = InternalState()
    state.current_base_coin_availability = INITIAL_INVESTMENT

    # Gather the data
    print("[INFO] Gathering data")
    (data_ts, data_date, data_price) = read_log_file(LOG_FILE)

    # Plot the data
    fig, ax = plt.subplots()
    ax.plot(data_date, data_price)

    # Find the first location in the data which has enough previous samples to compute the average
    starting_index = 0
    first_ts = data_ts[0]
    for i in range(len(data_ts)):
        if data_ts[i] > first_ts + AVG_HRS * 60 * 60:
            starting_index = i
            break

    # Find the first location in the data which has enough previous samples to compute the short average
    starting_index_short = 0
    first_ts = data_ts[0]
    for i in range(len(data_ts)):
        if data_ts[i] > first_ts + SHORT_AVG_HRS * 60 * 60:
            starting_index_short = i
            break

    # Find the first location in the data which has enough previous samples to compute the long average
    starting_index_long = 0
    first_ts = data_ts[0]
    for i in range(len(data_ts)):
        if data_ts[i] > first_ts + LONG_AVG_HRS * 60 * 60:
            starting_index_long = i
            break

    # Compute the absolute starting index that is correct for every average
    overall_starting_index = max(
        starting_index_long, starting_index, starting_index_short)

    # Compute the initial average
    state.considered_avg = compute_avg_price(
        data_ts, data_price, AVG_HRS, data_ts[overall_starting_index])
    state.considered_short_avg = compute_avg_price(
        data_ts, data_price, SHORT_AVG_HRS, data_ts[overall_starting_index])
    state.considered_long_avg = compute_avg_price(
        data_ts, data_price, LONG_AVG_HRS, data_ts[overall_starting_index])

    # Accumulate average data
    avg_price = []
    avg_short_price = []
    avg_long_price = []
    avg_thr = []
    avg_time = []

    # Run the simulator
    for i in range(overall_starting_index, len(data_ts)):
        # print(
        #     f"[INFO] Simulation progress: {float(100.0 * (i - starting_index) / (len(data_ts) - starting_index)):.2f}%")

        # Populate the equivalent state
        state.timestamp = data_ts[i]
        state.current_price = data_price[i]

        # Propagate the average by multiplying with the number of considered values, subtracting the
        # first of the previously considered ones and adding the new one
        state.considered_avg = ((state.considered_avg * starting_index) -
                                data_price[i - starting_index] + data_price[i]) / starting_index
        state.considered_short_avg = ((state.considered_short_avg * starting_index_short) -
                                      data_price[i - starting_index_short] + data_price[i]) / starting_index_short
        state.considered_long_avg = ((state.considered_long_avg * starting_index_long) -
                                     data_price[i - starting_index_long] + data_price[i]) / starting_index_long

        # Update price ratios
        state.last_price_ratio = state.current_price_ratio
        state.current_price_ratio = state.considered_short_avg / state.considered_long_avg

        # Populate the average samples
        avg_price.append(state.considered_avg)
        avg_short_price.append(state.considered_short_avg)
        avg_long_price.append(state.considered_long_avg)
        avg_thr.append(state.considered_avg *
                       (1 - (MIN_DELTA + BUY_TAX + SELL_TAX) / 100.0))
        avg_time.append(dt.datetime.fromtimestamp(state.timestamp))

        # Make the strategic decision
        decision = make_decision(state, config)

        # Update the internal state
        if decision == Action.BUY:
            investment = min(
                state.current_base_coin_availability, MAX_INVESTMENT)
            state.current_base_coin_availability -= investment

            state.last_buy_price = state.current_price
            state.current_coin_availability = (investment -
                                               (BUY_TAX / 100.0) * investment) / state.current_price
            state.last_action = decision
            state.last_action_ts = state.timestamp
            ax.axvline(data_date[i], color="b", label="BUY")

            # Report the buy action
            print(
                f"[{data_date[i]}]BUY action {config.BASE_CURRENCY_NAME}: {state.current_base_coin_availability:.2f} {config.CURRENCY_NAME}: {state.current_coin_availability:.8f}")

        elif decision == Action.SELL or decision == Action.SELL_LOSS:
            investment = state.current_coin_availability
            state.last_action = decision
            state.current_base_coin_availability += state.current_coin_availability * state.current_price - \
                (config.SELL_TAX / 100.0) * \
                state.current_coin_availability * state.current_price
            state.current_coin_availability = 0
            state.last_action_ts = state.timestamp
            ax.axvline(data_date[i], color="g", label="SELL")

            # Report the sell action
            print(
                f"[{data_date[i]}]SELL action {config.BASE_CURRENCY_NAME}: {state.current_base_coin_availability:.2f} {config.CURRENCY_NAME}: {investment:.8f}")

    # Plot also the average considered price
    ax.plot(avg_time, avg_price, color="yellow")
    ax.plot(avg_time, avg_short_price, color="red")
    ax.plot(avg_time, avg_long_price, color="orange")
    # ax.plot(avg_time, avg_thr, color="blue")
    plt.show()


if __name__ == "__main__":
    main()
