from configuration_reader import *
from investment_strategy import *
import matplotlib.pyplot as plt
import datetime as dt
import time

# Not important for the actual simulation, only important for the backend algorithm who MAY decide
# for specific actions based on how much it is farming money
INITIAL_INVESTMENT = 100


class SimulationData:
    timestamp = 0
    action = Action.NONE
    price = 0.0


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


def simulate(config: UserConfiguration, data_ts, data_price) -> list:
    simulation_result = []

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

    # Compute the initial average
    state.considered_avg = compute_avg_price(
        data_ts, data_price, config.AVG_HRS, data_ts[starting_index])

    # Run the simulator
    for i in range(starting_index, len(data_ts)):

        # Populate the equivalent state
        state.timestamp = data_ts[i]
        state.current_price = data_price[i]

        # Propagate the average by multiplying with the number of considered values, subtracting the
        # first of the previously considered ones and adding the new one
        state.considered_avg = ((state.considered_avg * starting_index) -
                                data_price[i - starting_index] + data_price[i]) / starting_index

        # Make the strategic decision
        decision = make_decision(state, config)

        # Update the internal state
        if decision == Action.BUY:
            investment = state.current_base_coin_availability
            state.current_base_coin_availability -= investment

            state.last_buy_price = state.current_price
            state.current_coin_availability = (investment -
                                               (config.BUY_TAX / 100.0) * investment) / state.current_price
            state.last_action = decision
            state.last_action_ts = state.timestamp

            # Register the simulation step
            data_point = SimulationData()
            data_point.timestamp = state.timestamp
            data_point.action = Action.BUY
            data_point.price = state.current_price
            simulation_result.append(data_point)

        elif decision == Action.SELL or decision == Action.SELL_LOSS:
            investment = state.current_coin_availability
            state.last_action = decision

            value = state.current_coin_availability * state.current_price
            state.current_base_coin_availability += value - \
                (config.SELL_TAX / 100.0) * value

            state.current_coin_availability = 0
            state.last_action_ts = state.timestamp

            # Register the simulation step
            data_point = SimulationData()
            data_point.timestamp = state.timestamp
            data_point.action = Action.SELL
            data_point.price = state.current_price
            simulation_result.append(data_point)

    return simulation_result
