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
    # Number of seconds from beginning / number of seconds in 30 minutes
    number_candles = (avg_hrs * 60 * 60) // (30 * 60)
    data = client.klines(coin_name, "30m", limit=number_candles)

    # Sum the average among open and close prices
    result = 0.0
    for candle in data:
        open = candle[1]
        close = candle[4]
        result += (float(open) + float(close)) / 2.0

    # Average the final result
    result = result / len(data)

    return truncate(result, 8)
