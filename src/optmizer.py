from simulator import *


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
    config.AVG_HRS = AVG_HRS
    config.COIN_NAME = COIN_NAME
    config.CURRENCY_NAME = CURRENCY_NAME
    config.BASE_CURRENCY_NAME = BASE_CURRENCY_NAME
    config.MIN_GAIN = MIN_GAIN
    config.BUY_TAX = BUY_TAX
    config.SELL_TAX = SELL_TAX
    config.MIN_DELTA = MIN_DELTA
    config.STOP_LOSS = STOP_LOSS
    config.SLEEP_DAYS_AFTER_LOSS = SLEEP_DAYS_AFTER_LOSS

    print(simulate(config))


if __name__ == "__main__":
    main()
