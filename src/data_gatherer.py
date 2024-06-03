from coinbase_interface import *
from configuration_reader import *
from logger import *
import datetime as dt
import time

SIMULATION_DAYS = 365
COIN_NAME = "BTC-EUR"
KEY_FILE_NAME = "key.json"


class LoggedData(LoggableObject):
    timestamp = 0
    unix_date = 0
    price = 0.0


def gather_data(client: RESTClient, coin_name: str, starting_timestamp: int):
    # A max of 300 samples can be requested
    current_time = starting_timestamp
    delta_seconds = 300 * 60
    iterations = int(SIMULATION_DAYS * 24.0 * 60.0 / 300.0)

    data_collection_ts = []
    data_collection_dates = []
    data_collection_price = []

    counter = 0
    while counter < iterations:
        try:
            print(
                f"[INFO] Data gathering: {(100.0 * counter / iterations):.2f}%")
            # Retrieve the data candles
            data = client.get_candles(
                coin_name, current_time - (iterations - counter) * delta_seconds, current_time - (iterations - counter - 1) * delta_seconds, "ONE_MINUTE")

            # Pack them from top to bottom (the candles are sorted such that the most recent time is the first element)
            for i in range(len(data["candles"])):
                candle = data["candles"][len(data["candles"]) - 1 - i]
                data_collection_ts.append(int(candle["start"]))
                data_collection_dates.append(
                    dt.datetime.fromtimestamp(int(candle["start"])))
                data_collection_price.append(float(candle["open"]))

            counter += 1
        except Exception as e:
            print(f"[ERR] Error retrieving simulation data: {str(e)}")
            time.sleep(1)

    return (data_collection_ts, data_collection_dates, data_collection_price)


def main():
    # Setup the API client
    client = RESTClient(key_file=get_absolute_path(
        "../" + KEY_FILE_NAME))

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
        data.price = data_prices[i]

        # Log the data into the file
        log_data(get_absolute_path("../history.csv"), data)


if __name__ == "__main__":
    main()
