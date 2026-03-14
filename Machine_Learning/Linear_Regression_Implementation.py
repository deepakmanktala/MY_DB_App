import pandas as pd
from sklearn.datasets import load_boston
from sklearn.datasets import fetch_openml
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import fetch_california_housing
from sklearn.datasets import fetch_openml

housing = fetch_openml(name="house_prices", as_frame=True)

housing = fetch_california_housing()

data_url = "http://lib.stat.cmu.edu/datasets/boston"
raw_df = pd.read_csv(data_url, sep="\s+", skiprows=22, header=None)
data = np.hstack([raw_df.values[::2, :], raw_df.values[1::2, :2]])
target = raw_df.values[1::2, 2]


df = load_boston()
print(df.head())
# fetch_openml()


