import pandas as pd
import sys
import csv


class PatentData:
    def __init__(self, file: str, sep: str):
        self.data = None
        self.file = file
        self.sep = sep

    def load_dataset(self):
        max_int = sys.maxsize
        while True:
            try:
                csv.field_size_limit(max_int)
                break
            except OverflowError:
                max_int = int(max_int / 10)

        self.data = pd.read_csv(self.file, sep=self.sep)

    def restruct_data(self, columns: list[str]):
        self.data = self.data[columns]

    def query(self, cond: dict[str: any], output: list[str]):
        found_data = self.data
        for column, value in cond.items():
            found_data = found_data[found_data[column] == value]
        return found_data[output].to_numpy().tolist()
