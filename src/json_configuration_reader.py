from pathlib import Path
from enum import Enum
from typing import List
import json
import os


class AlgorithmType(Enum):
    THRESHOLD = "THRESHOLD"
    CROSSOVER = "CROSSOVER"
    DERIVATIVE = "DERIVATIVE"


class UserConfiguration:
    ALGORITHM_TYPE = AlgorithmType.THRESHOLD
    COIN_NAME = ""
    CURRENCY_NAME = ""
    BASE_CURRENCY_NAME = ""
    AVG_HRS = 0
    SHORT_AVG_HRS = 0
    LONG_AVG_HRS = 0
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


def read_user_configurations(path: str) -> List[UserConfiguration]:
    # Read the Json configuration file
    script_location = Path(__file__).absolute().parent
    file_location = script_location / path

    if not os.path.exists(file_location):
        raise Exception("[Err] The configuration file does not exist")

    # Parse json file
    file = file_location.open()
    data = json.load(file)

    # Read the configurations
    configs = []

    # Populate the resulting configurations
    for row in data["CONFIGS"]:
        # Detect the algorithm type and assign the correct configuration values
        if str(row["ALGORITHM_TYPE"]).lower() == AlgorithmType.THRESHOLD.value.lower():
            config = UserConfiguration()
            config.ALGORITHM_TYPE = AlgorithmType.THRESHOLD
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
            config.TEST_MODE = row["TEST_MODE"]
        elif str(row["ALGORITHM_TYPE"]).lower() == AlgorithmType.CROSSOVER.value.lower():
            config = UserConfiguration()
            config.ALGORITHM_TYPE = AlgorithmType.CROSSOVER
            config.COIN_NAME = row["COIN_NAME"]
            config.CURRENCY_NAME = row["CURRENCY_NAME"]
            config.BASE_CURRENCY_NAME = row["BASE_CURRENCY_NAME"]
            config.AVG_HRS = int(row["AVG_HRS"])
            config.SHORT_AVG_HRS = int(row["SHORT_AVG_HRS"])
            config.LONG_AVG_HRS = int(row["LONG_AVG_HRS"])
            config.BUY_TAX = float(row["BUY_TAX"])
            config.SELL_TAX = float(row["SELL_TAX"])
            config.MIN_DELTA = float(row["MIN_DELTA"])
            config.STOP_LOSS = float(row["STOP_LOSS"])
            config.SLEEP_DAYS_AFTER_LOSS = int(row["SLEEP_DAYS_AFTER_LOSS"])
            config.KEY_FILE_NAME = row["KEY_FILE_NAME"]
            config.LOG_NAME = row["LOG_NAME"]
            config.TEST_MODE = row["TEST_MODE"]
        elif str(row["ALGORITHM_TYPE"]).lower() == AlgorithmType.DERIVATIVE.value.lower():
            config = UserConfiguration()
            config.ALGORITHM_TYPE = AlgorithmType.DERIVATIVE
            config.COIN_NAME = row["COIN_NAME"]
            config.CURRENCY_NAME = row["CURRENCY_NAME"]
            config.BASE_CURRENCY_NAME = row["BASE_CURRENCY_NAME"]
            config.AVG_HRS = int(row["AVG_HRS"])
            config.BUY_TAX = float(row["BUY_TAX"])
            config.SELL_TAX = float(row["SELL_TAX"])
            config.STOP_LOSS = float(row["STOP_LOSS"])
            config.SLEEP_DAYS_AFTER_LOSS = int(row["SLEEP_DAYS_AFTER_LOSS"])
            config.KEY_FILE_NAME = row["KEY_FILE_NAME"]
            config.LOG_NAME = row["LOG_NAME"]
            config.TEST_MODE = row["TEST_MODE"]
        else:
            raise Exception("[Err] The algorithm type does not exist")

        # Add config to the list
        configs.append(config)

    return configs
