from pathlib import Path
import matplotlib.pyplot as plt
import datetime as dt
import csv
import os

LOG_FILE = "../execution_logs/ETC.log"
DELTA_BUY = 1.2


def read_log_file(path: str) -> tuple[list, list, list, list]:
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
    data_avg = []
    data_unix = []
    data_action = []
    for row in reader:
        data_ts.append(int(row["timestamp"]))
        data_price.append(float(row["current_price"]))
        data_avg.append(float(row["considered_avg"]))
        data_unix.append(dt.datetime.fromtimestamp(int(row["timestamp"])))
        data_action.append(row["last_action"])

    file.close()
    return (data_ts, data_unix, data_price, data_avg, data_action)


def main():
    fig, ax = plt.subplots()

    (data_ts, data_unix, data_price, data_avg,
     data_action) = read_log_file(LOG_FILE)

    ax.plot(data_unix, data_price)
    ax.plot(data_unix, data_avg, color="yellow")

    # Generate buy/sell vertical lines
    for i in range(1, len(data_action)):
        if data_action[i] != data_action[i-1]:
            if "BUY" in data_action[i]:
                ax.axvline(data_unix[i], color="b", label="BUY")
            elif "SELL" in data_action[i]:
                ax.axvline(data_unix[i], color="g", label="SELL")

    # Generate the threshold under which the invester buys
    data_buy_thr = []
    for i in range(len(data_avg)):
        data_buy_thr.append(data_avg[i] - data_avg[i] * DELTA_BUY / 100.0)

    ax.plot(data_unix, data_buy_thr, color="red")

    plt.show()


if __name__ == "__main__":
    main()
