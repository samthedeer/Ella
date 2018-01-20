import os
import fnmatch
import json
import sqlite3 as sql
from datetime import datetime
import pytz


from models.brain import Brain
from gekko import Trader
from scripts.market_data import download_market_data
from scripts.tickers import get_tickers


def timestamp_to_local(ts):
    tz = pytz.timezone('Australia/Melbourne')
    return datetime.fromtimestamp(ts, tz)


def config_exists():
    if os.path.exists(os.path.join(os.getcwd(), 'config.json')):
        return True
    else:
        with open("config.json", 'w+') as json_file:
            json.dump(dict(), json_file)
            return


def get_config(name):
    config_exists()
    with open("config.json", 'r') as json_file:
        cfg = json.load(json_file)
        try:
            return cfg[name]
        except TypeError:
            print('Cannot find location in config, please enter full path')


def set_config(name, value):
    config_exists()
    with open('config.json', 'r') as json_file:
        config = json.load(json_file)
    config[name] = value

    # write it back to the file
    with open('config.json', 'w') as json_file:
        json.dump(config, json_file)


def walk_gekko_history(history_location):
    for root, dir, files in os.walk(history_location):
        return fnmatch.filter(files, '*.db')


def get_gekko_location(user_input):
    if not user_input:
        return get_config('location')
    elif user_input:
        path = os.path.normpath(user_input)
        set_config('location', path)
        return path


def get_gekko_history_location():
    while True:
        user_input = input('please enter the filepath to gekko installation: ')
        gekko_location = os.path.join(get_gekko_location(user_input), 'history')
        if not os.path.isdir(gekko_location):
            print('Error, no path found')
            get_gekko_history_location()
        return gekko_location


def get_db_trading_pair(directory, db_name):
    con = sql.connect(os.path.join(directory, db_name))
    cursor = con.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    table = [t[0] for t in cursor.fetchall() if t[0].startswith('candles')]
    con.close()
    return ''.join(table[0].split('_')[1:]), table[0]


def get_db_time_range(directory, db_name, table_name):
    con = sql.connect(os.path.join(directory, db_name))
    cursor = con.cursor()
    cursor.execute('SELECT start FROM ' + table_name)
    first = cursor.fetchone()
    cursor.execute('SELECT start FROM ' + table_name + ' ORDER BY id DESC')
    last = cursor.fetchone()
    con.close()
    return first[0], last[0]


def get_gekko_db_info(directory, dbs):
    gekko_db_list = []
    for db in dbs:
        pair, table_name = get_db_trading_pair(directory, db)
        first, last = get_db_time_range(directory, db, table_name)
        start = timestamp_to_local(first)
        end = timestamp_to_local(last)
        d = dict(pair=pair, start=start, end=end, dbname=db, tablename=table_name, directory=directory)
        gekko_db_list.append(d)
    return gekko_db_list


def run_trader(data):
    trader = Trader(data)
    brain = Brain(trader.actions, trader.data)
    brain.run_simulation()

    con = sql.connect(os.path.join(data['directory'], data['dbname']))
    cursor = con.cursor()
    cursor.execute('SELECT close FROM {} ORDER BY id DESC'.format(data['tablename']))
    last_close = cursor.fetchone()[0]
    final_value = trader.get_current_value(last_close)

    if final_value > trader.current_best:
        neurons = [str(neuron) for neuron in brain.neurons]
        trader.update_results(neurons, final_value)


if __name__ == "__main__":
    gekko_history_location = get_gekko_history_location()
    gekko_dbs = walk_gekko_history(gekko_history_location)
    db_list = get_gekko_db_info(gekko_history_location, gekko_dbs)
    for idx, db in enumerate(db_list):
        print('{} - {} From: {} To: {}'.format(idx+1, db['pair'], db['start'], db['end']))
    while True:
        choice = input('Please choose a dataset from above (number): ')
        if choice == '' and get_config('choice'):
            choice = get_config('choice')
        try:
            if int(choice) - 1 < 0:
                raise IndexError
            set_config('choice', int(choice))
            choice = db_list[int(choice) - 1]
            break
        except ValueError:
            print('Not a number')
        except IndexError:
            print('Not a valid number')

    for _ in range(1000):
        run_trader(choice)
