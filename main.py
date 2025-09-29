import pandas as pd

prices_df = pd.read_csv("./car_prices.csv")
prices_df = prices_df.drop(["trim", "transmission", "vin", "color", "interior"], axis=1)
prices_df = prices_df.dropna()

# print(prices_df.info())
# print(prices_df.describe())
# print(prices_df)
# print(prices_df["state"].unique())
# for val in prices_df['seller'].unique():
#    print(val)

# Define keywords that identify rental companies
rental_keywords = [
    "rent", "rental", "rac", "u-save", "u save",
    "enterprise", "hertz", "avis", "budget", "thrifty",
    "sixt", "fox", "economy", "elrac", "ez rent", "superior auto rental"
]


def is_rental(line):
    text = line.lower()
    return any(keyword in text for keyword in rental_keywords)


prices_df["isrental"] = prices_df['seller'].apply(is_rental)
# print(prices_df)
