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

# Step 1: Compute total sales volume per year, make, model
volume_df = prices_df.groupby(["year", "make", "model"], as_index=False).agg(
    total_volume=("sellingprice", "count")
)

# Step 2: Define high-volume threshold (top 25%)
threshold = volume_df["total_volume"].quantile(0.75)
high_volume_models = volume_df[volume_df["total_volume"] > threshold]

# Step 3: Filter main dataframe
filtered_df = prices_df.merge(
    high_volume_models[["year", "make", "model"]],
    on=["year", "make", "model"],
    how="inner"
)

# Step 4: Group by sale_year, year, make, model and compute avg_price
grouped_df = filtered_df.groupby(
    ["sale_year", "year", "make", "model"], as_index=False
).agg(avg_price=("sellingprice", "mean"))

# Step 5: Pivot for plotting
pivot_df = grouped_df.pivot_table(
    index="sale_year",
    columns=["year", "make", "model"],
    values="avg_price"
)

# Step 6: Keep only significant upward trends (>=10% increase)
growth_threshold = 0.20  # 10%
growth_dict = {}
significant_cols = []

for col in pivot_df.columns:
    series = pivot_df[col].dropna()
    if series.size > 1:
        first, last = series.iloc[0], series.iloc[-1]
        growth = (last - first) / first
        if growth >= growth_threshold:
            significant_cols.append(col)
            growth_dict[col] = growth

pivot_df = pivot_df[significant_cols]

# Step 7: Highlight top 10 models by total growth
top_cols = sorted(growth_dict, key=growth_dict.get, reverse=True)[:10]
others_cols = [col for col in pivot_df.columns if col not in top_cols]

# Step 8: Plot
plt.figure(figsize=(14, 8))
palette = sns.color_palette("tab20", n_colors=len(top_cols))

# Plot top models with colors
for i, col in enumerate(top_cols):
    plt.plot(pivot_df.index, pivot_df[col], alpha=0.9, linewidth=2,
             color=palette[i], label=f"{col[1]} {col[2]} ({col[0]})")

# Plot remaining models as faint gray
for col in others_cols:
    plt.plot(pivot_df.index, pivot_df[col],
             alpha=0.3, linewidth=1, color="gray", zorder=0)

plt.xlabel("Sale Year")
plt.ylabel("Average Price")
plt.title(
    f"Average Price Trends for Top 25% High-Volume Models (≥{int(growth_threshold*100)}% Increase)")
plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left", fontsize="small")
plt.grid(True)
plt.tight_layout()
plt.show()
