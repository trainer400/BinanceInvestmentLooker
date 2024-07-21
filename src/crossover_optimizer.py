from binance_interface import *
from simulator import *
import decimal
import itertools
import multiprocessing
import csv


LOG_FILE = "../execution_logs/PEPEUSDT-120.csv"
COIN_NAME = "PEPEUSDT"
CURRENCY_NAME = "PEPE"
BASE_CURRENCY_NAME = "USDT"
BUY_TAX = 0.1
SELL_TAX = 0.1
STOP_LOSS = 50
SLEEP_DAYS_AFTER_LOSS = 30

# Create user configuration
config = UserConfiguration()
config.ALGORITHM_TYPE = AlgorithmType.CROSSOVER
config.AVG_HRS = 1
config.LONG_AVG_HRS = 2
config.COIN_NAME = COIN_NAME
config.CURRENCY_NAME = CURRENCY_NAME
config.BASE_CURRENCY_NAME = BASE_CURRENCY_NAME
config.BUY_TAX = BUY_TAX
config.SELL_TAX = SELL_TAX
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


def objective(params):
    avg_hrs, long_avg_hrs = params

    # Invalid cases are rejected
    if avg_hrs >= long_avg_hrs or avg_hrs == 0 or long_avg_hrs == 0:
        return (0, 0, 0)

    config.AVG_HRS = float(avg_hrs)
    config.LONG_AVG_HRS = float(long_avg_hrs)

    simulation_data = simulate(config, data_ts, data_price)
    score = evaluate_simulation(config, simulation_data)

    return (avg_hrs, long_avg_hrs, score)


def main():
    AVG_HRS_MIN = 0.1
    AVG_HRS_MAX = 30
    AVG_HRS_STEP = 1

    LONG_AVG_HRS_MIN = 0.1
    LONG_AVG_HRS_MAX = 50
    LONG_AVG_HRS_STEP = 1

    avg_hrs = list[float](drange(AVG_HRS_MIN, AVG_HRS_MAX, str(AVG_HRS_STEP)))
    avg_long_hrs = list[float](
        drange(LONG_AVG_HRS_MIN, LONG_AVG_HRS_MAX, str(LONG_AVG_HRS_STEP)))

    # Create the set of combinations
    param_combinations = list(itertools.product(avg_hrs, avg_long_hrs))

    # In parallel look for the best result
    with multiprocessing.Pool() as pool:
        results = pool.map(objective, param_combinations)

    # look for the best result
    best = 0
    for i in range(len(results)):
        if results[i][2] > results[best][2]:
            best = i

    print(
        f"Best config ({results[best][2]}): {results[best][0]} [HRS], {results[best][1]} [LONG_HRS]")


if __name__ == "__main__":
    main()
