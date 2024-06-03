from configuration_reader import *
from investment_strategy import *
from coinbase_interface import *
import matplotlib.pyplot as plt
import datetime as dt
import time

INITIAL_INVESTMENT = 100
LOG_FILE = "../logs/ETC-USD-1YR.csv"
COIN_NAME = "ETC-USDC"
CURRENCY_NAME = "ETC"
BASE_CURRENCY_NAME = "USDC"
AVG_HRS = 20
MIN_GAIN = 1.5
BUY_TAX = 0.1
SELL_TAX = 0.1
MIN_DELTA = 3
STOP_LOSS = 50
SLEEP_DAYS_AFTER_LOSS = 30
MAX_INVESTMENT = 300
LEVER = 4


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
        data_price.append(float(row["price"]))
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
    config.AVG_HRS = AVG_HRS
    config.COIN_NAME = COIN_NAME
    config.CURRENCY_NAME = CURRENCY_NAME
    config.BASE_CURRENCY_NAME = BASE_CURRENCY_NAME
    config.MIN_GAIN = MIN_GAIN
    config.BUY_TAX = BUY_TAX
    config.SELL_TAX = SELL_TAX
    config.MIN_DELTA = MIN_DELTA
    config.STOP_LOSS = STOP_LOSS / LEVER
    config.SLEEP_DAYS_AFTER_LOSS = SLEEP_DAYS_AFTER_LOSS

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

    # Compute the initial average
    state.considered_avg = compute_avg_price(
        data_ts, data_price, AVG_HRS, data_ts[starting_index])

    # Accumulate average data
    avg_price = []
    avg_time = []

    # Lever debit if present
    lever_debit = 0

    # Run the simulator
    for i in range(starting_index, len(data_ts)):
        # print(
        #     f"[INFO] Simulation progress: {float(100.0 * (i - starting_index) / (len(data_ts) - starting_index)):.2f}%")

        # Populate the equivalent state
        state.timestamp = data_ts[i]
        state.current_price = data_price[i]

        # Propagate the average by multiplying with the number of considered values, subtracting the
        # first of the previously considered ones and adding the new one
        state.considered_avg = ((state.considered_avg * starting_index) -
                                data_price[i - starting_index] + data_price[i]) / starting_index

        # Populate the average samples
        avg_price.append(state.considered_avg)
        avg_time.append(dt.datetime.fromtimestamp(state.timestamp))

        # Make the strategic decision
        decision = make_decision(state, config)

        # Update the internal state
        if decision == Action.BUY:
            investment = min(
                state.current_base_coin_availability, MAX_INVESTMENT)
            state.current_base_coin_availability -= investment

            # Adjust the investment depending on the LEVER
            investment = investment * LEVER
            lever_debit = (1 - 1.0/LEVER) * investment

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
            state.current_base_coin_availability -= lever_debit
            state.current_coin_availability = 0
            state.last_action_ts = state.timestamp
            ax.axvline(data_date[i], color="g", label="SELL")

            # Report the sell action
            print(
                f"[{data_date[i]}]SELL action {config.BASE_CURRENCY_NAME}: {state.current_base_coin_availability:.2f} {config.CURRENCY_NAME}: {investment:.8f}")

    # Plot also the average considered price
    ax.plot(avg_time, avg_price, color="yellow")
    plt.show()


if __name__ == "__main__":
    main()
