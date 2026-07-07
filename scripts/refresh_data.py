import argparse, os, random, sys
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
RAW_DATA_PATH = os.path.join(PROJECT_ROOT, 'data', 'raw_trains.csv')
DB_PATH = os.path.join(PROJECT_ROOT, 'data', 'railway.db')

POPULAR_ROUTES = [
    ('New Delhi','Mumbai Central'),('New Delhi','Kolkata Howrah'),
    ('New Delhi','Chennai Central'),('Mumbai Central','Bengaluru City'),
    ('Chennai Central','Hyderabad Deccan'),('Kolkata Howrah','Patna Junction'),
    ('New Delhi','Jaipur Junction'),('Mumbai Central','Ahmedabad Junction'),
    ('New Delhi','Lucknow Charbagh'),('Bengaluru City','Chennai Central'),
    ('Pune Junction','Secunderabad'),('New Delhi','Chandigarh'),
    ('Kolkata Howrah','Bhubaneswar'),('Mumbai Central','Pune Junction'),
    ('New Delhi','Agra Cantt'),
]
TRAIN_TYPES = ['Express','Passenger','Superfast']
TRAIN_TYPE_WEIGHTS = [0.50, 0.30, 0.20]
TRAIN_NAME_PREFIXES = ['Rajdhani','Shatabdi','Duronto','Garib Rath','Jan Shatabdi','Mail','Express','Superfast','Intercity','Passenger','Sampark Kranti','Humsafar','Tejas','Vande Bharat']
MONTH_TO_SEASON = {1:'Winter',2:'Winter',3:'Summer',4:'Summer',5:'Summer',6:'Monsoon',7:'Monsoon',8:'Monsoon',9:'Post-Monsoon',10:'Post-Monsoon',11:'Post-Monsoon',12:'Winter'}

def generate_new_records(n):
    records = []
    today = datetime.now()
    for _ in range(n):
        tn = str(random.randint(10000,99999))
        tt = random.choices(TRAIN_TYPES, weights=TRAIN_TYPE_WEIGHTS, k=1)[0]
        name = f'{random.choice(TRAIN_NAME_PREFIXES)} {tt}'
        src, dst = random.choice(POPULAR_ROUTES)
        if random.random() < 0.3: src, dst = dst, src
        route = f'{src} to {dst}'
        days_back = random.randint(0, 6)
        date = today - timedelta(days=days_back)
        season = MONTH_TO_SEASON[date.month]
        dh = random.randint(5,22)
        dm = random.choice([0,5,10,15,20,25,30,35,40,45,50,55])
        sd = date.replace(hour=dh, minute=dm, second=0)
        th = random.randint(3,20)
        sa = sd + timedelta(hours=th, minutes=random.randint(0,59))
        delay = max(0, int(np.random.exponential(scale=15)))
        ad = sd + timedelta(minutes=delay)
        arv_delay = max(0, delay + random.randint(-5,10))
        aa = sa + timedelta(minutes=arv_delay)
        records.append({'train_number':tn,'train_name':name,'source_station':src,'destination_station':dst,'route':route,'scheduled_departure':sd.strftime('%Y-%m-%d %H:%M:%S'),'actual_departure':ad.strftime('%Y-%m-%d %H:%M:%S'),'scheduled_arrival':sa.strftime('%Y-%m-%d %H:%M:%S'),'actual_arrival':aa.strftime('%Y-%m-%d %H:%M:%S'),'delay_minutes':delay,'train_type':tt,'date':date.strftime('%Y-%m-%d'),'season':season})
    return pd.DataFrame(records)

def refresh(new_records=200):
    print('='*55)
    print(f'  DATA REFRESH - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
    print('='*55)
    print(f'\n[1/4] Generating {new_records} new records...')
    new_df = generate_new_records(new_records)
    print('[2/4] Appending to raw CSV...')
    if os.path.exists(RAW_DATA_PATH):
        existing = pd.read_csv(RAW_DATA_PATH)
        combined = pd.concat([existing, new_df], ignore_index=True)
        combined.to_csv(RAW_DATA_PATH, index=False)
        print(f'  Raw CSV: {len(existing)} -> {len(combined)} rows')
    else:
        new_df.to_csv(RAW_DATA_PATH, index=False)
        print(f'  Raw CSV created with {len(new_df)} rows')
    print('[3/4] Re-running data cleaning pipeline...')
    sys.path.insert(0, SCRIPT_DIR)
    import clean_data
    import importlib
    importlib.reload(clean_data)
    clean_data.main()
    print('\n[4/4] Verifying refresh...')
    if os.path.exists(DB_PATH):
        import sqlite3
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM trains')
        total = cur.fetchone()[0]
        cur.execute('SELECT MIN(date), MAX(date) FROM trains')
        dr = cur.fetchone()
        conn.close()
        print(f'  Database: {total} total records')
        print(f'  Date range: {dr[0]} to {dr[1]}')
    print('\nData refresh complete!')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Refresh railway dataset with new records')
    parser.add_argument('--records', type=int, default=200, help='Number of new records (default: 200)')
    args = parser.parse_args()
    refresh(new_records=args.records)
