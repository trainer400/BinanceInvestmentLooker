from configuration_reader import *
from binance_interface import *
from investment_strategy import *
import datetime as dt
import time
import pickle
import sys
import json


def load_internal_state(config: UserConfiguration):
    file_path = get_absolute_path(
        "../internal_states/" + config.LOG_NAME + ".state")
    state = InternalState()
    state.last_action = Action.NONE
    state.last_buy_price = 0
    state.last_action_ts = 0

    # If the file does not exist, return the default internal state
    if not os.path.exists(file_path):
        print("[INFO] Non pre existing internal state log file, returning default one")
        return state

    # Open the binary file
    log = open(file_path, "rb")

    # Load the binary state
    state = pickle.load(log)
    log.close()

    return state


def save_internal_state(config: UserConfiguration, state: InternalState):
    file_path = get_absolute_path(
        "../internal_states/" + config.LOG_NAME + ".state")

    # Create the file
    log = open(file_path, "wb")

    # Save the struct
    pickle.dump(state, log)
    log.close()


def compute_base_coin_availability(client, config: UserConfiguration, configs, states):
    # In case the last operation is a BUY, the base coin for this instance is 0
    if states[config.LOG_NAME].last_action == Action.BUY:
        return 0

    # Sum up all the investments which should have access to the base coin and divide for them
    counter = 0

    for conf in configs:
        # The investment should have deposited his part and the base currency type must be the same
        if states[conf.LOG_NAME].last_action != Action.BUY and conf.BASE_CURRENCY_NAME == config.BASE_CURRENCY_NAME:
            counter += 1

    # Get the amount of base currency
    base_currency = get_coin_availability(client, config.BASE_CURRENCY_NAME)

    # Divide equally the amount of base currency available
    return truncate(base_currency / counter, 2)


def compute_coin_availability(client, config: UserConfiguration, configs, states):
    # In case the last operation is a SELL / SELL_LOSS or NONE, the coin for this instance is 0
    if states[config.LOG_NAME].last_action == Action.SELL or \
        states[config.LOG_NAME].last_action == Action.SELL_LOSS or \
            states[config.LOG_NAME].last_action == Action.NONE:
        return 0

    # Sum up all the investments which should have access to the investment coin and divide for them
    counter = 0

    for conf in configs:
        # The investment should have bought his part and the investment currency type must be the same
        if states[conf.LOG_NAME].last_action == Action.BUY and conf.CURRENCY_NAME == config.CURRENCY_NAME:
            counter += 1

    # Get the amount of investment currency
    currency = get_coin_availability(client, config.CURRENCY_NAME)

    # Divide equally the amount of base currency available
    return truncate(currency / counter, 8)


def main():
    # Delay on startup
    time.sleep(10)

    # Set the std output to a log file
    new_stdout = open(get_absolute_path("../console.log"), "a")
    sys.stdout = new_stdout
    sys.stderr = new_stdout

    # Read the user configuration
    configs = read_user_configurations("../invester_config.csv")

    # Load the internal states
    states = {}
    for config in configs:
        state = load_internal_state(config)
        states[config.LOG_NAME] = state

    # Update loop
    while True:
        for config in configs:
            # Setup the API client
            with open(get_absolute_path("../" + config.KEY_FILE_NAME), 'rb') as key_file:
                key = key_file.read()
                key = json.loads(key)

            # Create the client REST object
            client = Spot(api_key=key["APIKey"], private_key=key["privateKey"])

            # Init the internal state
            state = states[config.LOG_NAME]

            try:
                # Update the internal state with fresh data
                state.timestamp = get_server_timestamp(client)
                state.current_price = get_current_price(
                    client, config.COIN_NAME)
                state.current_coin_availability = compute_coin_availability(
                    client, config, configs, states)
                state.current_base_coin_availability = compute_base_coin_availability(
                    client, config, configs, states)
                state.considered_avg = get_avg_price(
                    client, config.COIN_NAME, config.AVG_HRS, state.timestamp)

                # Make decision
                decision = make_decision(state, config)

                # Actuate the decision
                if decision == Action.BUY:
                    # Buy coins
                    action_result = (True, "")

                    if not config.TEST_MODE:
                        action_result = buy_coin(client, config.COIN_NAME,
                                                 state.current_base_coin_availability)

                    if action_result[0]:
                        # Register the purchase details
                        state.last_buy_price = state.current_price
                        state.last_action = decision
                        state.last_action_ts = state.timestamp

                        # Log the event
                        log_data(get_absolute_path(
                            "../execution_logs/" + config.LOG_NAME + ".ev"), state)
                    else:
                        print(
                            f"[{state.timestamp}][{dt.datetime.fromtimestamp(state.timestamp)}][ERR][BUY] Error during buy transaction: {action_result[1]}")

                elif decision == Action.SELL or decision == Action.SELL_LOSS:
                    # Sell coins
                    action_result = (True, "")

                    if not config.TEST_MODE:
                        action_result = sell_coin(client, config.COIN_NAME,
                                                  state.current_coin_availability)

                    if action_result[0]:
                        # Register the sell details
                        state.last_action = decision
                        state.last_action_ts = state.timestamp

                        # Log the event
                        log_data(get_absolute_path(
                            "../execution_logs/" + config.LOG_NAME + ".ev"), state)
                    else:
                        print(
                            f"[{state.timestamp}][{dt.datetime.fromtimestamp(state.timestamp)}][ERR][SELL] Error during sell transaction: {action_result[1]}")

                # Save the internal in case of a restart
                save_internal_state(config, state)

                # Log the internal state
                log_data(get_absolute_path(
                    "../execution_logs/" + config.LOG_NAME + ".log"), state)
                print(
                    f"[{state.timestamp}][{dt.datetime.fromtimestamp(state.timestamp)}][INFO] Logged data")

                # Flush the console log
                new_stdout.flush()

            except Exception as e:
                print(
                    f"[{state.timestamp}][{dt.datetime.fromtimestamp(state.timestamp)}][ERR] Caught unhandled exception during the process: {str(e)}")

        # Sleep until next update
        time.sleep(10)


if __name__ == "__main__":
    main()
