from pathlib import Path
import csv
import os


class UserConfiguration:
    COIN_NAME = ""
    CURRENCY_NAME = ""
    BASE_CURRENCY_NAME = ""
    AVG_HRS = 0
    MIN_GAIN = 0.0
    BUY_TAX = 0.0
    SELL_TAX = 0.0
    MIN_DELTA = 0.0
    STOP_LOSS = 0
    SLEEP_DAYS_AFTER_LOSS = 0
    KEY_FILE_NAME = ""
    LOG_NAME = ""
    TEST_MODE = False


def get_absolute_path(path: str):
    script_location = Path(__file__).absolute().parent
    file_location = script_location / path
    return str(file_location)


def read_user_configurations(path: str):
    # Read the CSV configuration file
    script_location = Path(__file__).absolute().parent
    file_location = script_location / path

    # Verify the configuration file presence
    if not os.path.exists(file_location):
        raise Exception("[ERR] The configuration file does not exist")

    file = file_location.open()
    reader = csv.DictReader(file)

    # Read all the csv rows
    rows = []
    for row in reader:
        rows.append(row)

    # Check the presence of a valid config row
    if len(rows) < 1:
        raise Exception("[ERR] No valid configuration")

    configs = []

    # Populate the resulting configurations
    for row in rows:
        config = UserConfiguration()
        config.COIN_NAME = row["COIN_NAME"]
        config.CURRENCY_NAME = row["CURRENCY_NAME"]
        config.BASE_CURRENCY_NAME = row["BASE_CURRENCY_NAME"]
        config.AVG_HRS = int(row["AVG_HRS"])
        config.MIN_GAIN = float(row["MIN_GAIN"])
        config.BUY_TAX = float(row["BUY_TAX"])
        config.SELL_TAX = float(row["SELL_TAX"])
        config.MIN_DELTA = float(row["MIN_DELTA"])
        config.STOP_LOSS = float(row["STOP_LOSS"])
        config.SLEEP_DAYS_AFTER_LOSS = int(row["SLEEP_DAYS_AFTER_LOSS"])
        config.KEY_FILE_NAME = row["KEY_FILE_NAME"]
        config.LOG_NAME = row["LOG_NAME"]
        config.TEST_MODE = False if row["TEST_MODE"] == '0' else True

        if config.AVG_HRS >= 150 or config.AVG_HRS <= 0:
            raise Exception(
                "[ERR] Invalid AVG HRS time must be of interval (0:150)")

        # Add config to the list
        configs.append(config)

    return configs
