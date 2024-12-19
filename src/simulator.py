import copy
from investment_strategy import *
import matplotlib.pyplot as plt
import datetime as dt
import time

# Not important for the actual simulation, only important for the backend algorithm who MAY decide
# for specific actions based on how much it is farming money
INITIAL_INVESTMENT = 100


def compute_avg_price(data_ts: list, data_price: list, avg_hrs: int, starting_timestamp: int):
    # Delta in seconds that the requested average impacts on the timestamp
    delta_seconds = avg_hrs * 60 * 60

    # Sum all the prices that correspond to a timestamp that is inside the considered average window
    result = 0
    counter = 0
    for i in range(len(data_ts)):
        if data_ts[i] < starting_timestamp and data_ts[i] > starting_timestamp - delta_seconds:
            result += data_price[i]
            counter += 1
        elif data_ts[i] > starting_timestamp:
            break
    return float(result) / counter


def simulate(config: UserConfiguration, data_ts, data_price) -> list[InternalState]:
    # Check configuration
    if config.SHORT_AVG_HRS > config.LONG_AVG_HRS and config.LONG_AVG_HRS != 0 and config.SHORT_AVG_HRS:
        print("[ERR] Long average is less than small average")
        return

    # Create an internal state to use during the simulation
    state = InternalState()
    state.current_base_coin_availability = INITIAL_INVESTMENT

    # Find the first location in the data which has enough previous samples to compute the average
    starting_index = 0
    first_ts = data_ts[0]
    for i in range(len(data_ts)):
        if data_ts[i] > first_ts + config.AVG_HRS * 60 * 60:
            starting_index = i
            break

    # Find the first location in the data which has enough previous samples to compute the long average
    starting_index_short = 0
    if config.SHORT_AVG_HRS != 0:
        first_ts = data_ts[0]
        for i in range(len(data_ts)):
            if data_ts[i] > first_ts + config.SHORT_AVG_HRS * 60 * 60:
                starting_index_short = i
                break

    # Find the first location in the data which has enough previous samples to compute the long average
    starting_index_long = 0
    if config.LONG_AVG_HRS != 0:
        first_ts = data_ts[0]
        for i in range(len(data_ts)):
            if data_ts[i] > first_ts + config.LONG_AVG_HRS * 60 * 60:
                starting_index_long = i
                break

    # Compute the highest index from which the simulation shall start
    absolute_starting_index = max(
        starting_index, starting_index_long, starting_index_short)

    # Compute initial average
    state.considered_avg = compute_avg_price(
        data_ts, data_price, config.AVG_HRS, data_ts[absolute_starting_index])

    # Compute the initial short average
    if config.SHORT_AVG_HRS != 0:
        state.considered_short_avg = compute_avg_price(
            data_ts, data_price, config.SHORT_AVG_HRS, data_ts[absolute_starting_index])

    # Compute the initial long average
    if config.LONG_AVG_HRS != 0:
        state.considered_long_avg = compute_avg_price(
            data_ts, data_price, config.LONG_AVG_HRS, data_ts[absolute_starting_index])

    simulation_result = [InternalState() for i in range(
        len(data_ts) - absolute_starting_index)]

    # Run the simulator
    for i in range(absolute_starting_index, len(data_ts)):

        # Populate the equivalent state
        state.timestamp = data_ts[i]
        state.current_price = data_price[i]

        # Propagate the average by multiplying with the number of considered values, subtracting the
        # first of the previously considered ones and adding the new one
        avg = ((state.considered_avg * starting_index) -
               data_price[i - starting_index] + data_price[i]) / starting_index
        state.current_delta = avg - state.considered_avg
        state.considered_avg = avg

        # Update long and short average
        if config.LONG_AVG_HRS != 0 and config.SHORT_AVG_HRS != 0:
            state.considered_long_avg = ((state.considered_long_avg * starting_index_long) -
                                         data_price[i - starting_index_long] + data_price[i]) / starting_index_long

            state.considered_short_avg = ((state.considered_short_avg * starting_index_short) -
                                          data_price[i - starting_index_short] + data_price[i]) / starting_index_short
            # Update price ratios
            state.last_price_ratio = state.current_price_ratio
            state.current_price_ratio = state.considered_short_avg / state.considered_long_avg

        # Make the strategic decision
        decision = make_decision(state, config)

        # Update the internal state
        if decision == Action.BUY:
            investment = state.current_base_coin_availability
            state.last_action = decision

            state.last_buy_price = state.current_price
            state.current_coin_availability = (investment -
                                               (config.BUY_TAX / 100.0) * investment) / state.current_price

            state.current_base_coin_availability = 0
            state.last_action_ts = state.timestamp

        elif decision == Action.SELL or decision == Action.SELL_LOSS:
            investment = state.current_coin_availability
            state.last_action = decision

            value = state.current_coin_availability * state.current_price
            state.current_base_coin_availability += value - \
                (config.SELL_TAX / 100.0) * value

            state.current_coin_availability = 0
            state.last_action_ts = state.timestamp

        # Register the simulation step
        index = i - absolute_starting_index
        simulation_result[index].timestamp = state.timestamp
        simulation_result[index].current_price = state.current_price
        simulation_result[index].current_coin_availability = state.current_coin_availability
        simulation_result[index].current_base_coin_availability = state.current_base_coin_availability
        simulation_result[index].current_price_ratio = state.current_price_ratio
        simulation_result[index].last_price_ratio = state.last_price_ratio
        simulation_result[index].considered_avg = state.considered_avg
        simulation_result[index].considered_short_avg = state.considered_short_avg
        simulation_result[index].considered_long_avg = state.considered_long_avg
        simulation_result[index].last_action = state.last_action
        simulation_result[index].last_action_ts = state.last_action_ts
        simulation_result[index].last_buy_price = state.last_buy_price
        simulation_result[index].current_delta = state.current_delta
        simulation_result[index].last_delta = state.last_delta

        # Update the last derivative
        state.last_delta = state.current_delta

    return simulation_result
