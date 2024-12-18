from logger import *
from json_configuration_reader import *
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
    current_price_ratio = 0
    last_price_ratio = 0
    considered_avg = 0
    considered_short_avg = 0
    considered_long_avg = 0
    last_action = Action.NONE
    last_action_ts = 0
    last_buy_price = 0


def make_threshold_decision(state: InternalState, config: UserConfiguration):
    # The user has crypto in its account
    if state.last_action == Action.BUY:
        # If the expected gain is greater than the threshold, suggest to sell
        if (1 - (state.last_buy_price / state.current_price)) > (config.MIN_GAIN / 100.0):
            return Action.SELL
        if config.STOP_LOSS != 0 and (1 - state.considered_avg / state.last_buy_price) > (config.STOP_LOSS / 100.0):
            return Action.SELL_LOSS
    elif (state.last_action != Action.SELL_LOSS or state.timestamp - state.last_action_ts > config.SLEEP_DAYS_AFTER_LOSS * 24 * 60 * 60) and \
            state.current_price <= (state.considered_avg - state.considered_avg * ((config.BUY_TAX + config.SELL_TAX + config.MIN_DELTA) / 100.0)) and \
            state.current_base_coin_availability != 0:
        return Action.BUY

    return Action.NONE


def make_crossover_decision(state: InternalState, config: UserConfiguration):
    # The user has crypto in the account
    if state.last_action == Action.BUY:
        # The little average crosses the bigger average and the price is greater than the buy one thus sell
        if state.current_price_ratio <= 1 and state.last_price_ratio > 1 and (state.current_price / state.last_buy_price > (1 + (config.BUY_TAX + config.SELL_TAX) / 100)):
            return Action.SELL
        if config.STOP_LOSS != 0 and (1 - state.considered_avg / state.last_buy_price) > (config.STOP_LOSS / 100.0):
            return Action.SELL_LOSS
    elif (state.last_action != Action.SELL_LOSS or state.timestamp - state.last_action_ts > config.SLEEP_DAYS_AFTER_LOSS * 24 * 60 * 60) and \
            state.current_price <= (state.considered_avg - state.considered_avg * ((config.BUY_TAX + config.SELL_TAX + config.MIN_DELTA) / 100.0)) and \
            state.current_base_coin_availability != 0:
        return Action.BUY
    return Action.NONE


def make_decision(state: InternalState, config: UserConfiguration):
    # Select the decision method depending on the algorithm type
    if config.ALGORITHM_TYPE == AlgorithmType.THRESHOLD:
        return make_threshold_decision(state, config)
    elif config.ALGORITHM_TYPE == AlgorithmType.CROSSOVER:
        return make_crossover_decision(state, config)

    return Action.NONE
