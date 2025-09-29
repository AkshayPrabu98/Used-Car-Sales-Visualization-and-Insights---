import matplotlib.pyplot as plt
from datetime import datetime
import pandas as pd

prices_df = pd.read_csv("./car_prices.csv")
prices_df = prices_df.drop(
    ["trim", "transmission", "vin", "color", "interior"], axis=1)
prices_df = prices_df.dropna()


def parse_js_date(date_str):
    try:
        # Strip the timezone name in parentheses, keep the GMT offset
        date_str = " ".join(date_str.split(" ")[:6])
        return datetime.strptime(date_str, "%a %b %d %Y %H:%M:%S GMT%z")
    except Exception:
        return pd.NaT


prices_df["saledate"] = prices_df["saledate"].apply(parse_js_date)
prices_df["saledate"] = pd.to_datetime(
    prices_df["saledate"], utc=True, errors="coerce")
prices_df = prices_df.dropna(subset=["saledate"])
prices_df["saledate"] = prices_df["saledate"].dt.tz_localize(None)

canada_codes = {
    "ab", "bc", "mb", "nb", "nl", "ns", "on", "pe", "qc", "sk", "nt", "nu", "yt"
}

prices_df = prices_df[~prices_df["state"].isin(canada_codes)]

prices_df["make"] = prices_df["make"].str.lower()
prices_df["model"] = prices_df["model"].str.lower()
prices_df["body"] = prices_df["body"].str.lower()
prices_df["seller"] = prices_df["seller"].str.lower()

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
# print(grouped_df.info())
# print(grouped_df.head())

prices_df["saleyear"] = prices_df["saledate"].dt.year

grouped_df = prices_df.groupby(
    ["saleyear", "make", "model"], as_index=False
).agg(
    avgprice=("sellingprice", "mean"),
    salesvolume=("sellingprice", "count")
)
# print(grouped_df.info())
# print(grouped_df.head())

# Compute total sales volume per make+model across all years
volume_df = prices_df.groupby(["make", "model"], as_index=False).agg(
    totalvolume=("sellingprice", "count")
)

# Compute quartiles
q1 = volume_df["totalvolume"].quantile(0.25)
q2 = volume_df["totalvolume"].quantile(0.5)
q3 = volume_df["totalvolume"].quantile(0.75)

# Define filters for 2nd and 3rd quartiles
second_quartile = volume_df[(volume_df["totalvolume"] > q1) & (
    volume_df["totalvolume"] <= q2)]
third_quartile = volume_df[(volume_df["totalvolume"] > q2) & (
    volume_df["totalvolume"] <= q3)]


def plot_quartile(quartile_df, title):
    # Keep only the models in this quartile
    df = prices_df.merge(
        quartile_df[["make", "model"]],
        on=["make", "model"],
        how="inner"
    )
    # Group by year, make, model
    grouped_df = df.groupby(
        ["saleyear", "make", "model"], as_index=False
    ).agg(avgprice=("sellingprice", "mean"))

    # Pivot for plotting
    pivot_df = grouped_df.pivot_table(
        index="saleyear",
        columns=["make", "model"],
        values="avgprice"
    )

    # Plot
    plt.figure(figsize=(14, 8))
    for col in pivot_df.columns:
        plt.plot(pivot_df.index, pivot_df[col], alpha=0.7)
    plt.xlabel("Year")
    plt.ylabel("Average Price")
    plt.title(title)
    plt.grid(True)
    plt.show()


# Plot each quartile separately
plot_quartile(second_quartile,
              "Average Price Trends: 2nd Quartile of Sales Volume")
plot_quartile(third_quartile,
              "Average Price Trends: 3rd Quartile of Sales Volume")
