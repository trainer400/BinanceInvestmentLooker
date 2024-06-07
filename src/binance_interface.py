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
    # Number of seconds from beginning / number of seconds in 5 minutes
    number_candles = (avg_hrs * 60 * 60) // (5 * 60)
    data = client.klines(coin_name, "5m", limit=min(number_candles, 1000))

    # Sum the average among open and close prices
    result = 0.0
    for candle in data:
        open = candle[1]
        close = candle[4]
        result += (float(open) + float(close)) / 2.0

    # Average the final result
    result = result / len(data)

    return truncate(result, 8)


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
                              type="MARKET", quantity=f"{amount:.8f}", timestamp=timestamp)

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
