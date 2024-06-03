from logger import *
from configuration_reader import *
from enum import Enum


class Action(Enum):
    NONE = 0
    BUY = 1
    SELL = 2
    SELL_LOSS = 3


class InternalState(LoggableObject):
    timestamp = 0
    current_price = 0
    current_coin_availability = 0
    current_base_coin_availability = 0
    considered_avg = 0
    last_action = Action.NONE
    last_action_ts = 0
    last_buy_price = 0


def make_decision(state: InternalState, config: UserConfiguration):
    # The user has bitcoins in its account
    if state.last_action == Action.BUY:
        # If the expected gain is greater than the threshold, suggest to sell
        if (1 - (state.last_buy_price / state.current_price)) > (config.MIN_GAIN / 100.0):
            return Action.SELL
        if config.STOP_LOSS != 0 and (1 - state.considered_avg / state.last_buy_price) > (config.STOP_LOSS / 100.0):
            return Action.SELL_LOSS
    elif (state.last_action != Action.SELL_LOSS or state.timestamp - state.last_action_ts > config.SLEEP_DAYS_AFTER_LOSS * 24 * 60 * 60) and \
            state.current_price < (state.considered_avg - state.considered_avg * ((config.BUY_TAX + config.SELL_TAX + config.MIN_DELTA) / 100.0)) and \
            state.current_base_coin_availability != 0:
        return Action.BUY

    return Action.NONE
