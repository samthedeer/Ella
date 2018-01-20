import os
from utils.tools import read_json, write_json


class Trader:

    def __init__(self, data):
        self.ticker = data['pair']
        self.output_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), f"output{os.sep}{self.ticker}.json")
        self.btc = 10
        self.current_best = self.get_current_best()
        self.data = data
        self.portfolio = []
        self.actions = {
            'BUY': lambda coin: self.buy(coin),
            'SELL': lambda coin: self.sell(coin['close'])
        }

        if not os.path.exists(self.output_file):
            open(self.output_file, 'a').close()

    def buy(self, coin):
        """
        Decrease BTC and add coin to portfolio
        """

        self.btc -= coin['close']
        self.portfolio.append(coin)

    def get_current_best(self):
        """
        Current best results
        """

        data = read_json(self.output_file)
        return data.get('results') if data.get('results') else 0

    def get_current_value(self, last_price):
        """
        Current value of account
        """

        portfolio_value = len(self.portfolio) * last_price
        return portfolio_value + self.btc

    def sell(self, last_price):
        """
        Increase BTC and remove coin from portfolio
        """

        if len(self.portfolio):
            self.btc += last_price
            self.portfolio.pop()

    def update_results(self, neurons, final_value):
        """
        Write results to JSON file 
        """

        print(
            f"\n{self.ticker} "
            f"\nNeurons: {neurons} "
            f"\nNew best: {final_value} "
            f"\nOld best: {self.current_best} "
        )
        self.current_best = final_value
        data = {'neurons': neurons, 'results': final_value}
        write_json(self.output_file, data)
