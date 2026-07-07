import os, sqlite3
import pandas as pd
import numpy as np

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
RAW_DATA_PATH = os.path.join(PROJECT_ROOT, 'data', 'raw_trains.csv')
CLEAN_DATA_PATH = os.path.join(PROJECT_ROOT, 'data', 'clean_trains.csv')
DB_PATH = os.path.join(PROJECT_ROOT, 'data', 'railway.db')
DATETIME_COLS = ['scheduled_departure','actual_departure','scheduled_arrival','actual_arrival']
MONTH_TO_SEASON = {1:'Winter',2:'Winter',3:'Summer',4:'Summer',5:'Summer',6:'Monsoon',7:'Monsoon',8:'Monsoon',9:'Post-Monsoon',10:'Post-Monsoon',11:'Post-Monsoon',12:'Winter'}

def load_raw_data(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"Raw data not found at '{path}'. Run 'python scripts/generate_data.py' first.")
    df = pd.read_csv(path)
    print(f"Loaded {len(df)} rows from {path}")
    return df

def remove_duplicates(df):
    before = len(df)
    df = df.drop_duplicates().reset_index(drop=True)
    print(f"Removed {before - len(df)} duplicates -> {len(df)} rows remaining")
    return df

def fix_datetime_formats(df):
    for col in DATETIME_COLS:
        df[col] = pd.to_datetime(df[col], format='mixed', dayfirst=True, errors='coerce')
    print("Fixed datetime formats")
    return df

def fix_date_column(df):
    df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
    print("Fixed date column")
    return df

def handle_missing_values(df):
    critical = ['train_number','date','source_station','destination_station']
    before = len(df)
    df = df.dropna(subset=critical).reset_index(drop=True)
    if before - len(df): print(f"Dropped {before - len(df)} rows with missing critical values")
    if df['delay_minutes'].isna().any():
        medians = df.groupby('train_type')['delay_minutes'].transform('median')
        df['delay_minutes'] = df['delay_minutes'].fillna(medians).round(0).astype(int)
        print("Filled missing delay_minutes with train-type median")
    for col in DATETIME_COLS:
        if df[col].isna().any():
            df = df.dropna(subset=[col]).reset_index(drop=True)
    if df['season'].isna().any() or (df['season']=='').any():
        df['season'] = df['date'].apply(lambda d: MONTH_TO_SEASON.get(d.month,'Unknown') if d else 'Unknown')
        print("Filled missing season values")
    print(f"Missing values after cleaning:\n{df.isna().sum().to_string()}")
    return df

def engineer_features(df):
    def cat(m):
        if m <= 5: return 'On-Time'
        elif m <= 20: return 'Minor Delay'
        else: return 'Major Delay'
    df['delay_category'] = df['delay_minutes'].apply(cat)
    df['day_of_week'] = df['date'].apply(lambda d: d.strftime('%A') if d else 'Unknown')
    df['month'] = df['date'].apply(lambda d: d.month if d else None)
    df['travel_duration_hours'] = ((df['scheduled_arrival']-df['scheduled_departure']).dt.total_seconds()/3600).round(2)
    df['year_month'] = df['date'].apply(lambda d: d.strftime('%Y-%m') if d else None)
    print("Engineered features: delay_category, day_of_week, month, travel_duration_hours, year_month")
    return df

def format_for_output(df):
    for col in DATETIME_COLS:
        df[col] = df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
    df['date'] = df['date'].astype(str)
    return df

def save_clean_csv(df, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    df.to_csv(path, index=False)
    print(f"Clean data saved -> {path} ({len(df)} rows)")

def load_to_database(df, db_path):
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    if os.path.exists(db_path): os.remove(db_path)
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("""CREATE TABLE trains (
        id INTEGER PRIMARY KEY AUTOINCREMENT, train_number TEXT NOT NULL,
        train_name TEXT NOT NULL, source_station TEXT NOT NULL,
        destination_station TEXT NOT NULL, route TEXT NOT NULL,
        scheduled_departure TEXT NOT NULL, actual_departure TEXT NOT NULL,
        scheduled_arrival TEXT NOT NULL, actual_arrival TEXT NOT NULL,
        delay_minutes INTEGER NOT NULL, train_type TEXT NOT NULL,
        date TEXT NOT NULL, season TEXT NOT NULL, delay_category TEXT NOT NULL,
        day_of_week TEXT NOT NULL, month INTEGER, travel_duration_hours REAL,
        year_month TEXT)""")
    cur.execute("CREATE INDEX idx_date ON trains(date)")
    cur.execute("CREATE INDEX idx_train_type ON trains(train_type)")
    cur.execute("CREATE INDEX idx_route ON trains(route)")
    cur.execute("CREATE INDEX idx_season ON trains(season)")
    conn.commit()
    df.to_sql('trains', conn, if_exists='append', index=False)
    print(f"Loaded {len(df)} rows into SQLite -> {db_path}")
    conn.close()

def run_analytics_queries(db_path):
    conn = sqlite3.connect(db_path)
    queries = {
        "1. Top 10 Busiest Routes": "SELECT route, COUNT(*) AS train_count FROM trains GROUP BY route ORDER BY train_count DESC LIMIT 10",
        "2. Average Delay by Train Type": "SELECT train_type, COUNT(*) AS total, ROUND(AVG(delay_minutes),1) AS avg_delay, ROUND(MAX(delay_minutes),1) AS max_delay FROM trains GROUP BY train_type ORDER BY avg_delay DESC",
        "3. Monthly Delay Trends": "SELECT year_month, COUNT(*) AS total, ROUND(AVG(delay_minutes),1) AS avg_delay FROM trains GROUP BY year_month ORDER BY year_month",
        "4. Top 10 Most Delayed Routes": "SELECT route, COUNT(*) AS cnt, ROUND(AVG(delay_minutes),1) AS avg_delay, SUM(CASE WHEN delay_minutes>20 THEN 1 ELSE 0 END) AS major FROM trains GROUP BY route HAVING cnt>=5 ORDER BY avg_delay DESC LIMIT 10",
        "5. On-Time Performance %": "SELECT train_type, COUNT(*) AS total, SUM(CASE WHEN delay_minutes<=5 THEN 1 ELSE 0 END) AS on_time, ROUND(100.0*SUM(CASE WHEN delay_minutes<=5 THEN 1 ELSE 0 END)/COUNT(*),1) AS on_time_pct FROM trains GROUP BY train_type",
        "6. Top 15 Source Stations": "SELECT source_station, COUNT(*) AS departures FROM trains GROUP BY source_station ORDER BY departures DESC LIMIT 15",
        "7. Seasonal Delay Patterns": "SELECT season, COUNT(*) AS total, ROUND(AVG(delay_minutes),1) AS avg_delay, SUM(CASE WHEN delay_minutes>20 THEN 1 ELSE 0 END) AS major, ROUND(100.0*SUM(CASE WHEN delay_minutes<=5 THEN 1 ELSE 0 END)/COUNT(*),1) AS on_time_pct FROM trains GROUP BY season ORDER BY avg_delay DESC",
        "8. Delay by Day of Week": "SELECT day_of_week, COUNT(*) AS total, ROUND(AVG(delay_minutes),1) AS avg_delay, SUM(CASE WHEN delay_minutes>20 THEN 1 ELSE 0 END) AS major FROM trains GROUP BY day_of_week ORDER BY avg_delay DESC",
        "9. Delay Category Distribution": "SELECT delay_category, COUNT(*) AS count, ROUND(100.0*COUNT(*)/(SELECT COUNT(*) FROM trains),1) AS pct FROM trains GROUP BY delay_category ORDER BY count DESC",
        "10. Longest Travel Duration": "SELECT route, ROUND(AVG(travel_duration_hours),1) AS avg_hours, COUNT(*) AS cnt FROM trains GROUP BY route HAVING cnt>=5 ORDER BY avg_hours DESC LIMIT 10",
    }
    print("\n" + "="*70 + "\n  RAILWAY ANALYTICS - SQL QUERY RESULTS\n" + "="*70)
    for title, query in queries.items():
        print(f"\n{title}\n{'-'*len(title)}")
        print(pd.read_sql_query(query, conn).to_string(index=False))
    conn.close()

def main():
    print("="*50 + "\n  Railway Data Cleaning Pipeline\n" + "="*50)
    df = load_raw_data(RAW_DATA_PATH)
    df = remove_duplicates(df)
    df = fix_datetime_formats(df)
    df = fix_date_column(df)
    df = handle_missing_values(df)
    df = engineer_features(df)
    df = format_for_output(df)
    save_clean_csv(df, CLEAN_DATA_PATH)
    load_to_database(df, DB_PATH)
    run_analytics_queries(DB_PATH)
    print("\nCleaning pipeline complete!")

if __name__ == '__main__':
    main()
