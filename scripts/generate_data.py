import os, random
from datetime import datetime, timedelta
import numpy as np
import pandas as pd

NUM_RECORDS = 1500
RANDOM_SEED = 42
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)
OUTPUT_PATH = os.path.join(PROJECT_ROOT, 'data', 'raw_trains.csv')
np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)

POPULAR_ROUTES = [
    ('New Delhi', 'Mumbai Central'), ('New Delhi', 'Kolkata Howrah'),
    ('New Delhi', 'Chennai Central'), ('Mumbai Central', 'Bengaluru City'),
    ('Chennai Central', 'Hyderabad Deccan'), ('Kolkata Howrah', 'Patna Junction'),
    ('New Delhi', 'Jaipur Junction'), ('Mumbai Central', 'Ahmedabad Junction'),
    ('New Delhi', 'Lucknow Charbagh'), ('Bengaluru City', 'Chennai Central'),
    ('Pune Junction', 'Secunderabad'), ('New Delhi', 'Chandigarh'),
    ('Kolkata Howrah', 'Bhubaneswar'), ('Mumbai Central', 'Pune Junction'),
    ('New Delhi', 'Agra Cantt'), ('Jaipur Junction', 'Ahmedabad Junction'),
    ('Chennai Central', 'Ernakulam Junction'), ('New Delhi', 'Amritsar Junction'),
    ('Lucknow Charbagh', 'Patna Junction'), ('Bengaluru City', 'Hyderabad Deccan'),
    ('New Delhi', 'Guwahati'), ('Mumbai Central', 'Nagpur Junction'),
    ('Kolkata Howrah', 'Ranchi'), ('Chennai Central', 'Madurai Junction'),
    ('New Delhi', 'Dehradun'), ('Ahmedabad Junction', 'Jaipur Junction'),
    ('Bengaluru City', 'Mysuru Junction'), ('Secunderabad', 'Vijayawada Junction'),
    ('Kanpur Central', 'Lucknow Charbagh'), ('New Delhi', 'Varanasi Junction'),
]
TRAIN_TYPES = ['Express', 'Passenger', 'Superfast']
TRAIN_TYPE_WEIGHTS = [0.50, 0.30, 0.20]
TRAIN_NAME_PREFIXES = [
    'Rajdhani', 'Shatabdi', 'Duronto', 'Garib Rath', 'Jan Shatabdi',
    'Mail', 'Express', 'Superfast', 'Intercity', 'Passenger',
    'Sampark Kranti', 'Humsafar', 'Tejas', 'Vande Bharat', 'Kisan',
    'Gatimaan', 'Vivek', 'Antyodaya', 'Uday', 'AC Express',
]
MONTH_TO_SEASON = {
    1:'Winter',2:'Winter',3:'Summer',4:'Summer',5:'Summer',
    6:'Monsoon',7:'Monsoon',8:'Monsoon',9:'Post-Monsoon',
    10:'Post-Monsoon',11:'Post-Monsoon',12:'Winter',
}

def gen_train_number():
    return str(random.randint(10000, 99999))

def gen_train_name(tt):
    return f'{random.choice(TRAIN_NAME_PREFIXES)} {tt}'

def gen_route():
    s, d = random.choice(POPULAR_ROUTES)
    if random.random() < 0.3: s, d = d, s
    return s, d

def gen_date():
    end = datetime(2025, 12, 31)
    start = datetime(2024, 1, 1)
    return start + timedelta(days=random.randint(0, (end - start).days))

def gen_times(date, tt):
    dh = random.randint(5, 22)
    dm = random.choice([0,5,10,15,20,25,30,35,40,45,50,55])
    sd = date.replace(hour=dh, minute=dm, second=0)
    if tt == 'Superfast': th = random.randint(2, 12)
    elif tt == 'Express': th = random.randint(4, 18)
    else: th = random.randint(6, 24)
    sa = sd + timedelta(hours=th, minutes=random.randint(0, 59))
    season = MONTH_TO_SEASON[date.month]
    if season == 'Monsoon': delay = int(np.random.exponential(scale=25))
    elif season == 'Winter': delay = int(np.random.exponential(scale=18))
    else: delay = int(np.random.exponential(scale=12))
    delay = max(0, min(delay, 180))
    ad = sd + timedelta(minutes=delay)
    arv_delay = max(0, delay + random.randint(-5, 10))
    aa = sa + timedelta(minutes=arv_delay)
    return sd, ad, sa, aa, delay

def generate_dataset(n=NUM_RECORDS):
    records = []
    pool = [gen_train_number() for _ in range(300)]
    for _ in range(n):
        tn = random.choice(pool)
        tt = random.choices(TRAIN_TYPES, weights=TRAIN_TYPE_WEIGHTS, k=1)[0]
        src, dst = gen_route()
        route = f'{src} \u2192 {dst}'
        date = gen_date()
        sd, ad, sa, aa, delay = gen_times(date, tt)
        records.append({
            'train_number': tn, 'train_name': gen_train_name(tt),
            'source_station': src, 'destination_station': dst, 'route': route,
            'scheduled_departure': sd.strftime('%Y-%m-%d %H:%M:%S'),
            'actual_departure': ad.strftime('%Y-%m-%d %H:%M:%S'),
            'scheduled_arrival': sa.strftime('%Y-%m-%d %H:%M:%S'),
            'actual_arrival': aa.strftime('%Y-%m-%d %H:%M:%S'),
            'delay_minutes': delay, 'train_type': tt,
            'date': date.strftime('%Y-%m-%d'), 'season': MONTH_TO_SEASON[date.month],
        })
    df = pd.DataFrame(records)
    mi = np.random.choice(df.index, size=int(n*0.02), replace=False)
    df.loc[mi, 'delay_minutes'] = np.nan
    di = np.random.choice(df.index, size=int(n*0.01), replace=False)
    df = pd.concat([df, df.loc[di]], ignore_index=True)
    bi = np.random.choice(df.index, size=10, replace=False)
    for idx in bi:
        d = pd.to_datetime(df.loc[idx, 'scheduled_departure'])
        df.loc[idx, 'scheduled_departure'] = d.strftime('%d/%m/%Y %H:%M')
    df = df.sample(frac=1, random_state=RANDOM_SEED).reset_index(drop=True)
    return df

if __name__ == '__main__':
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    print('Generating synthetic Indian Railways dataset...')
    df = generate_dataset()
    df.to_csv(OUTPUT_PATH, index=False)
    print(f'Generated {len(df)} records -> {OUTPUT_PATH}')


