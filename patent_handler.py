import pandas as pd
import sys
import csv

max_int = sys.maxsize
while True:
    try:
        csv.field_size_limit(max_int)
        break
    except OverflowError:
        max_int = int(max_int / 10)
data = pd.read_csv("data.csv", sep="╡")
