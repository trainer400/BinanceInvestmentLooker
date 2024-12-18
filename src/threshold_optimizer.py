import itertools
import multiprocessing
from binance_interface import *
from simulator import *
import decimal
import csv

LOG_FILE = "../execution_logs/PEPEUSDT-150.csv"
COIN_NAME = "PEPEUSDT"
CURRENCY_NAME = "PEPE"
BASE_CURRENCY_NAME = "USDT"
BUY_TAX = 0.1
SELL_TAX = 0.1
STOP_LOSS = 25
SLEEP_DAYS_AFTER_LOSS = 5

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


# Read the log file
(data_ts, data_unix, data_price) = read_log_file(LOG_FILE)


def evaluate_simulation(config: UserConfiguration, simulation_data: list[InternalState]):
    # Evaluate the final gain
    final_state = simulation_data[len(simulation_data) - 1]

    # In case at the end there is only a sell action, sell the remaining amount
    if (final_state.current_base_coin_availability == 0):
        final_state.current_base_coin_availability = final_state.current_coin_availability * \
            final_state.current_price

    return final_state.current_base_coin_availability


def objective(params):
    avg_hrs, min_gain, min_delta = params

    config.AVG_HRS = int(avg_hrs)
    config.MIN_GAIN = float(min_gain)
    config.MIN_DELTA = float(min_delta)

    simulation_data = simulate(config, data_ts, data_price)
    score = evaluate_simulation(config, simulation_data)

    print(
        f"Config ({score}): {avg_hrs} [AVG_HRS], {min_gain} [MIN_GAIN], {min_delta} [MIN_DELTA]")

    return (avg_hrs, min_gain, min_delta, score)


def main():
    AVG_HRS_MIN = 1
    AVG_HRS_MAX = 5
    AVG_HRS_STEP = 1

    # TODO drange spins off in a loop if the step is not multiple of 1 (other digits than 1)
    MIN_GAIN_MIN = 0.3
    MIN_GAIN_MAX = 2
    MIN_GAIN_STEP = 0.1

    MIN_DELTA_MIN = 0
    MIN_DELTA_MAX = 3.5
    MIN_DELTA_STEP = 0.1

    avg_hrs = list[float](range(AVG_HRS_MIN, AVG_HRS_MAX, AVG_HRS_STEP))
    min_gain = list[float](drange(MIN_GAIN_MIN, MIN_GAIN_MAX, MIN_GAIN_STEP))
    min_delta = list[float](
        drange(MIN_DELTA_MIN, MIN_DELTA_MAX, MIN_DELTA_STEP))

    # Create the set of combinations
    param_combinations = list(itertools.product(avg_hrs, min_gain, min_delta))

    # In parallel look for the best result
    with multiprocessing.Pool() as pool:
        results = pool.map(objective, param_combinations)

    # look for the best result
    best = 0
    for i in range(len(results)):
        if results[i][3] > results[best][3]:
            best = i

    print(
        f"Best config ({results[best][3]}): {results[best][0]} [AVG_HRS], {results[best][1]} [MIN_GAIN], {results[best][2]} [MIN_DELTA]")


if __name__ == "__main__":
    main()
