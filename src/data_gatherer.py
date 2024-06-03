from binance_interface import *
from configuration_reader import *
from logger import *
import datetime as dt
import time
import json

SIMULATION_DAYS = 365
COIN_NAME = "PEPEUSDT"
KEY_FILE_NAME = "key.json"


class LoggedData(LoggableObject):
    timestamp = 0
    unix_date = 0
    current_price = 0.0


def gather_data(client: Spot, coin_name: str, starting_timestamp: int):
    # A max of 1000 samples can be requested
    current_time = starting_timestamp
    delta_seconds = 1000 * 60
    iterations = int(SIMULATION_DAYS * 24.0 * 60.0 / 1000.0)

    data_collection_ts = []
    data_collection_dates = []
    data_collection_price = []

    counter = 0
    while counter < iterations:
        try:
            print(
                f"[INFO] Data gathering: {(100.0 * counter / iterations):.2f}%")
            # Retrieve the data candles
            data = client.klines(coin_name, "1m", startTime=(
                current_time - (iterations - counter) * delta_seconds) * 1000, limit=1000)

            # Pack them from top to bottom (the candles are sorted such that the most recent time is the first element)
            for i in range(len(data)):
                candle = data[i]
                data_collection_ts.append(candle[0] // 1000)
                data_collection_dates.append(
                    dt.datetime.fromtimestamp(candle[0] // 1000))
                data_collection_price.append(candle[1])

            counter += 1
        except Exception as e:
            print(f"[ERR] Error retrieving simulation data: {str(e)}")
            time.sleep(1)

    return (data_collection_ts, data_collection_dates, data_collection_price)


def main():
    # Load the key
    with open(get_absolute_path("../" + KEY_FILE_NAME), 'rb') as key_file:
        key = key_file.read()
    key = json.loads(key)

    # Setup the API client
    client = Spot(api_key=key["APIKey"], private_key=key["privateKey"])

    # Set the starting timestamp as the current one
    starting_timestamp = get_server_timestamp(client)

    # Gather the data from the server
    (data_ts, data_dates, data_prices) = gather_data(
        client, COIN_NAME, starting_timestamp)

    # Save the data into file
    for i in range(len(data_ts)):
        print(f"[INFO] Saving data: {(100.0 * i / len(data_ts)):.2f}%")

        data = LoggedData()
        data.timestamp = data_ts[i]
        data.unix_date = data_dates[i]
        data.current_price = data_prices[i]

        # Log the data into the file
        log_data(get_absolute_path("../history.csv"), data)


if __name__ == "__main__":
    main()
