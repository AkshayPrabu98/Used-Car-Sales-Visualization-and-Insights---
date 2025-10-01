import seaborn as sns
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
    if pd.isna(line):
        return False
    text = line.lower().strip()
    return any(keyword in text for keyword in rental_keywords)


prices_df["is_rental"] = prices_df['seller'].apply(is_rental)
# print(prices_df.info())
# print(prices_df.head())

prices_df["sale_year"] = prices_df["saledate"].dt.year

# Step 1: Filter for sale_year = 2015
df_2015 = prices_df[prices_df["sale_year"] == 2015]

# Step 2: Group by year, make, model
stats_2015 = df_2015.groupby(["year", "make", "model"], as_index=False).agg(
    avg_price=("sellingprice", "mean"),
    total_volume=("sellingprice", "count")
)

# Step 3: Sort by volume (optional, for readability)
stats_2015 = stats_2015.sort_values(
    "total_volume", ascending=False).head(20)  # top 20

# Step 4: Create combined bar + line plot
fig, ax1 = plt.subplots(figsize=(14, 8))

# Bar plot (sales volume)
ax1.bar(
    stats_2015["year"].astype(str) + " " +
    stats_2015["make"] + " " + stats_2015["model"],
    stats_2015["total_volume"],
    color="skyblue",
    alpha=0.7,
    label="Sales Volume"
)
ax1.set_ylabel("Sales Volume", color="blue")
ax1.tick_params(axis="y", labelcolor="blue")

# Create secondary axis for average price
ax2 = ax1.twinx()
ax2.plot(
    stats_2015["year"].astype(str) + " " +
    stats_2015["make"] + " " + stats_2015["model"],
    stats_2015["avg_price"],
    color="red",
    marker="o",
    linewidth=2,
    label="Average Price"
)
ax2.set_ylabel("Average Price (USD)", color="red")
ax2.tick_params(axis="y", labelcolor="red")

# Labels and formatting
plt.title("2015 Sales Volume (Bar) and Average Price (Line) by Year + Make + Model")
ax1.set_xticklabels(stats_2015["year"].astype(
    str) + " " + stats_2015["make"] + " " + stats_2015["model"], rotation=90)

# Combine legends
lines, labels = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines + lines2, labels + labels2, loc="upper right")

plt.tight_layout()
plt.show()
