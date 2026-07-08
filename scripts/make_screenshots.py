"""Generate README chart images from the SQLite data using matplotlib.

Produces PNGs into the screenshots/ folder to illustrate the dashboard in the
README without needing a live browser capture.
"""
import os
import sqlite3
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(PROJECT_ROOT, "data", "railway.db")
OUT_DIR = os.path.join(PROJECT_ROOT, "screenshots")
os.makedirs(OUT_DIR, exist_ok=True)

conn = sqlite3.connect(DB_PATH)
df = pd.read_sql_query("SELECT * FROM trains", conn)
conn.close()

plt.rcParams.update({"figure.dpi": 110, "font.size": 11})


def save(fig, name):
    path = os.path.join(OUT_DIR, name)
    fig.tight_layout()
    fig.savefig(path, bbox_inches="tight")
    plt.close(fig)
    print("saved", path)


# 1. Monthly delay trend (line)
monthly = (df.groupby("year_month")["delay_minutes"].mean()
           .reset_index().sort_values("year_month"))
fig, ax = plt.subplots(figsize=(10, 4.5))
ax.plot(monthly["year_month"], monthly["delay_minutes"], marker="o", color="#636EFA")
ax.set_title("Average Delay by Month")
ax.set_xlabel("Month")
ax.set_ylabel("Avg Delay (min)")
ax.grid(True, alpha=0.3)
plt.xticks(rotation=45, ha="right")
save(fig, "delay_trends.png")

# 2. Top 15 most delayed routes (horizontal bar)
rs = (df.groupby("route").agg(avg_delay=("delay_minutes", "mean"),
                              cnt=("train_number", "count")).reset_index())
rs = rs[rs["cnt"] >= 3].nlargest(15, "avg_delay").sort_values("avg_delay")
fig, ax = plt.subplots(figsize=(10, 6))
ax.barh(rs["route"], rs["avg_delay"], color="#EF553B")
ax.set_title("Top 15 Routes by Average Delay")
ax.set_xlabel("Avg Delay (min)")
save(fig, "route_analysis.png")

# 3. Seasonal delay heatmap (season x day of week)
day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
season_order = ["Winter", "Summer", "Monsoon", "Post-Monsoon"]
pivot = (df.groupby(["season", "day_of_week"])["delay_minutes"].mean()
         .reset_index()
         .pivot(index="season", columns="day_of_week", values="delay_minutes"))
pivot = pivot.reindex(index=[s for s in season_order if s in pivot.index],
                      columns=[d for d in day_order if d in pivot.columns])
fig, ax = plt.subplots(figsize=(9, 4.5))
im = ax.imshow(pivot.values, cmap="YlOrRd", aspect="auto")
ax.set_xticks(range(len(pivot.columns)))
ax.set_xticklabels(pivot.columns, rotation=45, ha="right")
ax.set_yticks(range(len(pivot.index)))
ax.set_yticklabels(pivot.index)
ax.set_title("Average Delay by Season & Day of Week")
fig.colorbar(im, ax=ax, label="Avg Delay (min)")
save(fig, "heatmap.png")

print("Done.")
