from binance.spot import Spot
import math


def truncate(num: float, decimals: int) -> float:
    result = num

    # No negative numbers are accepted
    decimals = abs(decimals)

    # Multiply the value and use math truncate to approximate it
    result = num * pow(10, decimals)
    result = math.trunc(result)

    return float(result) / pow(10, decimals)


def get_increment_from_string(increment: str):
    number = float(increment)

    # The counter is incremented every time we need to remove a 0
    counter = 0
    while number != 1:
        number *= 10
        counter += 1

    return counter


def get_current_price(client: Spot, coin_name: str):
    data = client.ticker_price(coin_name)
    return truncate(float(data["price"]), 8)


def get_coin_availability(client: Spot, currency_name: str):
    data = client.account()

    for balance in data["balances"]:
        if balance["asset"] == currency_name:
            amount = float(balance["free"])

            # Approximate in defect the amount (8 decimals)
            return truncate(amount, 8)
    return 0


def get_server_timestamp(client: Spot):
    data = client.time()

    # From milliseconds to seconds (unix time)
    return int(data["serverTime"]) // 1000


def get_avg_price(client: Spot, coin_name: str, avg_hrs: int, starting_timestamp: int):
    # Max number of candles that binance can send in one packet
    MAX_CANDLES = 1000

    # Number of seconds from beginning / number of seconds in 1 minute
    number_candles = (avg_hrs * 60 * 60) // 60

    # Starting timestamp to count the average
    target_timestamp = starting_timestamp - avg_hrs * 60 * 60

    # Iterate with 1m candles requests (to have the most precise estimation) until all the average hours are collected
    requested_candles = 0
    result = 0.0
    sum_number = 0
    while requested_candles < number_candles:
        # Request candles
        data = client.klines(coin_name, "1m",
                             endTime=(starting_timestamp - requested_candles * 60) * 1000, limit=min(number_candles - requested_candles, MAX_CANDLES))

        # Sum the average among open and close prices
        for candle in data:
            # Sum only if the candle timestamp is greater than the user requested one
            if (candle[0] / 1000 > target_timestamp):
                open = candle[1]
                close = candle[4]
                result += (float(open) + float(close)) / 2.0

                # Count the number of sums to make the average at the end
                sum_number += 1

        # Update the requested candles
        requested_candles += len(data)

    # Average the final result
    result = result / sum_number

    return truncate(result, 9)


def sell_coin(client: Spot, coin_name: str, amount: float) -> tuple:
    # Get the maximum precision that the API accepts for the coin
    filters = client.exchange_info(symbol=coin_name)["symbols"][0]["filters"]
    increment = 1

    # Look for the minimum increment
    for filter in filters:
        if filter["filterType"] == "LOT_SIZE":
            increment = get_increment_from_string(filter["stepSize"])
            break

    # Process the amount to truncate instead of approximate of the desired increment
    amount = truncate(amount, increment)

    # Get the order timestamp
    timestamp = get_server_timestamp(client)

    # Make the order (using formatted amount to avoid scientific notation)
    result = client.new_order(symbol=coin_name, side="SELL",
                              type="MARKET", quantity="{:.{prec}f}".format(amount, prec=increment), timestamp=timestamp)

    return (result["status"] == "FILLED", str(result))


def buy_coin(client: Spot, coin_name: str, amount: float) -> tuple:
    # Process the amount to truncate instead of approximate
    amount = truncate(amount, 2)

    # Get the order timestamp
    timestamp = get_server_timestamp(client)

    # Make the order
    result = client.new_order(symbol=coin_name, side="BUY", type="MARKET",
                              quoteOrderQty=amount, timestamp=timestamp)

    return (result["status"] == "FILLED", str(result))
