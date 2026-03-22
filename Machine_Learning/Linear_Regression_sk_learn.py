import pandas as pd
from pandas.core.interchange.dataframe_protocol import DataFrame
from sklearn.datasets import fetch_california_housing

from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
import numpy as np
import matplotlib.pyplot as plt

from sklearn.model_selection import cross_val_score
import seaborn as sns

df = fetch_california_housing()

#
# boston = load_boston()
# print(boston)

# print(housing)

# pd.DataFrame = (housing.data)

# print(pd.DataFrame.df)
print(df)

housing_dataset = pd.DataFrame(df.data)

print(housing_dataset)

housing_dataset.columns = df.feature_names

print(housing_dataset)
print(housing_dataset.head())

# data_housing = pd.DataFrame(df.data)
# print(housing_df)

## Independent Features and Dependent Features - X being  independent , y being depnedent

X = housing_dataset


y = df.target
# print(X)
#
# # pd.set_option('display.max_rows', None)
# # pd.set_option('display.max_columns', None)
# print(y)


# Train Tets split

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.3, random_state = 42)

print(X_train)
print(y_train)

# standardizing the dataset
scaler = StandardScaler()

X_train = scaler.fit_transform(X_train)

print ("##############################")
print(X_train)
X_test = scaler.transform(X_test)
regressor = LinearRegression()  ## Multi linear regresison
regressor.fit(X_train, y_train)
print(scaler.fit(X_train))

## Cross Validation
print(regressor.coef_)
print(regressor.intercept_)

regression = LinearRegression()
regression.fit(X_train, y_train)
print(regression.coef_)

mse = cross_val_score(regression, X_train, y_train, scoring='neg_mean_squared_error', cv=50)
print("###########################################")

print(mse)

np.mean(mse)

print(np.mean(mse))



### Prediction

reg_predict = regression.predict(X_test)
plt.show()
print(reg_predict)

displat = sns.displot(reg_predict - y_test)

plt.show()