from binance_interface import *
from simulator import *
import decimal
import copy
import csv

LOG_FILE = "../execution_logs/PEPEUSDT-120.csv"
COIN_NAME = "PEPEUSDT"
CURRENCY_NAME = "PEPE"
BASE_CURRENCY_NAME = "USDT"
BUY_TAX = 0.1
SELL_TAX = 0.1
STOP_LOSS = 50
SLEEP_DAYS_AFTER_LOSS = 30


def drange(x, y, jump):
    while x < y:
        yield truncate(float(x), get_increment_from_string(jump))
        x += float(decimal.Decimal(jump))


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


def evaluate_simulation(config: UserConfiguration, simulation_data: list):
    # Use 100% of initial investment
    initial_investment = 100

    # Evaluate the final gain
    base_coin = initial_investment
    active_coin = 0
    for data in simulation_data:
        if (data.action == Action.BUY):
            active_coin = (base_coin - (config.BUY_TAX / 100.0)
                           * base_coin) / data.price
            base_coin = 0

        elif (data.action == Action.SELL or data.action == Action.SELL_LOSS):
            value = active_coin * data.price
            base_coin = value - (config.SELL_TAX / 100.0) * value
            active_coin = 0

    # In case at the end there is only a sell action, sell the remaining amount
    if (base_coin == 0):
        base_coin = active_coin * \
            simulation_data[len(simulation_data) - 1].price

    return base_coin


def main():
    AVG_HRS_MIN = 1
    AVG_HRS_MAX = 15
    AVG_HRS_STEP = 1

    # TODO drange spins off in a loop if the step is not multiple of 1 (other digits than 1)
    MIN_GAIN_MIN = 0.3
    MIN_GAIN_MAX = 5
    MIN_GAIN_STEP = 0.1

    MIN_DELTA_MIN = 0
    MIN_DELTA_MAX = 5
    MIN_DELTA_STEP = 0.1

    # Create user configuration
    config = UserConfiguration()
    config.ALGORITHM_TYPE = AlgorithmType.THRESHOLD
    config.AVG_HRS = 1
    config.COIN_NAME = COIN_NAME
    config.CURRENCY_NAME = CURRENCY_NAME
    config.BASE_CURRENCY_NAME = BASE_CURRENCY_NAME
    config.MIN_GAIN = 3
    config.BUY_TAX = BUY_TAX
    config.SELL_TAX = SELL_TAX
    config.MIN_DELTA = 3.5
    config.STOP_LOSS = STOP_LOSS
    config.SLEEP_DAYS_AFTER_LOSS = SLEEP_DAYS_AFTER_LOSS

    # Read the log file
    (data_ts, data_unix, data_price) = read_log_file(LOG_FILE)

    # Best config
    best_config = config
    best_score = 0

    for avg_hrs in range(AVG_HRS_MIN, AVG_HRS_MAX, AVG_HRS_STEP):
        for min_gain in list(drange(MIN_GAIN_MIN, MIN_GAIN_MAX, str(MIN_GAIN_STEP))):
            for min_delta in list(drange(MIN_DELTA_MIN, MIN_DELTA_MAX, str(MIN_DELTA_STEP))):
                print(
                    f"Configuration: {avg_hrs} (AVG_HRS), {min_gain} (MIN_GAIN), {min_delta}  (MIN_DELTA)")

                # Set the config
                config.AVG_HRS = int(avg_hrs)
                config.MIN_GAIN = float(min_gain)
                config.MIN_DELTA = float(min_delta)

                simulation_data = simulate(config, data_ts, data_price)
                score = evaluate_simulation(config, simulation_data)

                if score > best_score:
                    best_score = score
                    best_config = copy.deepcopy(config)

                print(f"Score: {score}")
                print(
                    f"Best config ({best_score}): {best_config.AVG_HRS} [HRS], {best_config.MIN_GAIN} [MIN_GAIN], {best_config.MIN_DELTA} [MIN_DELTA]")


if __name__ == "__main__":
    main()
