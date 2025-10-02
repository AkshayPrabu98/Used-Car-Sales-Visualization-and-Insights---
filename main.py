from datetime import datetime
import matplotlib.pyplot as plt
import pandas as pd


def parse_js_date(date_str):
    try:
        date_str = " ".join(date_str.split(" ")[:6])  # strip timezone name
        return datetime.strptime(date_str, "%a %b %d %Y %H:%M:%S GMT%z")
    except Exception:
        return pd.NaT


# Rental keywords
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


# Load dataset
df_prices = pd.read_csv("./car_prices.csv")

# Drop unused columns
df_prices = df_prices.drop(
    ["trim", "transmission", "vin", "color", "interior"], axis=1
).dropna()

# Convert sale date to datetime
df_prices["saledate"] = df_prices["saledate"].apply(parse_js_date)
df_prices["saledate"] = pd.to_datetime(
    df_prices["saledate"], utc=True, errors="coerce")
df_prices = df_prices.dropna(subset=["saledate"])
df_prices["saledate"] = df_prices["saledate"].dt.tz_localize(None)

# Drop Canadian provinces
canada_codes = {"ab", "bc", "mb", "nb", "nl",
                "ns", "on", "pe", "qc", "sk", "nt", "nu", "yt"}
df_prices = df_prices[~df_prices["state"].isin(canada_codes)]

# Normalize strings
for col in ["make", "model", "body", "seller"]:
    df_prices[col] = df_prices[col].str.lower()

# Identify rental companies
df_prices["is_rental"] = df_prices['seller'].apply(is_rental)

# Add sale year
df_prices["sale_year"] = df_prices["saledate"].dt.year

# Filter for 2015
df_2015 = df_prices[df_prices["sale_year"] == 2015]

# Aggregate stats by (year, make, model)
df_2015_stats = df_2015.groupby(["year", "make", "model"], as_index=False).agg(
    avg_price=("sellingprice", "mean"),
    total_volume=("sellingprice", "count")
)

# Sort by sales volume and keep top 20
df_2015_stats = df_2015_stats.sort_values(
    "total_volume", ascending=False).head(20)

# Labels for x-axis
labels = df_2015_stats["year"].astype(
    str) + " " + df_2015_stats["make"] + " " + df_2015_stats["model"]

# --- Plot ---
fig, ax1 = plt.subplots(figsize=(14, 8))

# Bar plot (sales volume)
ax1.bar(
    range(len(df_2015_stats)),
    df_2015_stats["total_volume"],
    color="skyblue",
    alpha=0.7,
    label="Sales Volume"
)
ax1.set_ylabel("Sales Volume", color="blue")
ax1.tick_params(axis="y", labelcolor="blue")

# Secondary axis for average price
ax2 = ax1.twinx()
ax2.plot(
    range(len(df_2015_stats)),
    df_2015_stats["avg_price"],
    color="red",
    marker="o",
    linewidth=2,
    label="Average Price"
)
ax2.set_ylabel("Average Price (USD)", color="red")
ax2.tick_params(axis="y", labelcolor="red")

# Fix x-axis labels
ax1.set_xticks(range(len(df_2015_stats)))
ax1.set_xticklabels(labels, rotation=90)

# Title
plt.title("2015 Sales Volume (Bar) and Average Price (Line) by Year + Make + Model")

# Combine legends
lines, labels_1 = ax1.get_legend_handles_labels()
lines2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines + lines2, labels_1 + labels_2, loc="upper right")

plt.tight_layout()
plt.show()
