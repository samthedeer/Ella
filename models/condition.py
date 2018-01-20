import random
import sqlite3 as sql
from operator import gt, lt
from utils.tools import historical_values, operator_to_str


class Condition:

    def __init__(self, db_path, table_name):
        self.db_path = db_path
        self.table_name = table_name
        self.attribute = self.get_random_attribute()
        self.operator = self.get_random_operator()
        self.value = self.get_random_value()

    def __str__(self):
        return f"{self.attribute} {operator_to_str(self.operator)} {self.value}"

    def db_connection(self):
        try:
            con = sql.connect(self.db_path)
            return con
        except:
            return None

    def evaluate(self, row):
        """
        Evaluate row with condition
        """

        return self.operator(row[self.attribute], self.value)

    def get_random_attribute(self):
        """
        Random numeric attribute 
        """
        con = self.db_connection()
        con.row_factory = sql.Row
        cursor = con.cursor()
        cursor.execute("SELECT * from " + self.table_name)
        data = cursor.fetchone()
        con.close()
        return random.choice([k for k in data.keys() if k not in ['id', 'trades'] and isinstance(data[k], (int, float, complex))])

    @staticmethod
    def get_random_operator():
        """
        Random comparison operator
        """

        return random.choice([gt, lt])

    def get_random_value(self):
        """
        Random historical value for attribute
        """

        con = self.db_connection()
        con.row_factory = lambda c, row: row[0]
        cursor = con.cursor()
        cursor.execute("SELECT {} from {}".format(self.attribute, self.table_name))
        data = cursor.fetchall()

        return random.choice(data)
