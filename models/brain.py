import sqlite3 as sql
import os
from models.action import Action
from models.condition import Condition
from models.neuron import Neuron


class Brain:

    def __init__(self, actions, data):
        self.actions = [Action(name, event) for name, event in actions.items()]
        self.db_path = os.path.join(data['directory'], data['dbname'])
        self.table_name = data['tablename']

        self.neurons = [Neuron(action, Condition(self.db_path, self.table_name)) for action in self.actions]

    def result_generator(self, cursor, arraysize=100):
        """
        An iterator that uses fetchmany to keep memory usage down
        """
        while True:
            results = cursor.fetchmany(arraysize)
            if not results:
                break
            for result in results:
                yield result

    def run_simulation(self):
        """
        Iterate over the dataset row by row and invoke all action events (fire the neuron) if a condition is met
        """
        con = sql.connect(self.db_path)
        con.row_factory = sql.Row
        cursor = con.cursor()
        cursor.execute('select * from {}'.format(self.table_name))

        for row in self.result_generator(cursor):
            for neuron in self.neurons:
                neuron.signal(row)
