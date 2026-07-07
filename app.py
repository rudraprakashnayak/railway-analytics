import os, subprocess, sys, sqlite3
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title='Indian Railways Analytics Dashboard', page_icon='\U0001f686', layout='wide', initial_sidebar_state='expanded')

st.markdown("""
<style>
.kpi-card{background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);padding:20px;border-radius:12px;color:white;text-align:center;box-shadow:0 4px 15px rgba(0,0,0,0.1)}
.kpi-card.green{background:linear-gradient(135deg,#11998e 0%,#38ef7d 100%)}
.kpi-card.orange{background:linear-gradient(135deg,#f093fb 0%,#f5576c 100%)}
.kpi-card.blue{background:linear-gradient(135deg,#4facfe 0%,#00f2fe 100%)}
.kpi-card h3{margin:0;font-size:2rem;font-weight:700}
.kpi-card p{margin:5px 0 0 0;font-size:0.9rem;opacity:0.9}
</style>""", unsafe_allow_html=True)

PROJECT_ROOT = Path(__file__).resolve().parent
DB_PATH = PROJECT_ROOT / 'data' / 'railway.db'

def bootstrap_data():
    scripts_dir = PROJECT_ROOT / 'scripts'
    raw_csv = PROJECT_ROOT / 'data' / 'raw_trains.csv'
    if not raw_csv.exists():
        subprocess.run([sys.executable, str(scripts_dir / 'generate_data.py')], check=True, cwd=str(PROJECT_ROOT))
    if not DB_PATH.exists():
        subprocess.run([sys.executable, str(scripts_dir / 'clean_data.py')], check=True, cwd=str(PROJECT_ROOT))

@st.cache_data(ttl=300)
def load_data():
    if not DB_PATH.exists(): bootstrap_data()
    if not DB_PATH.exists():
        st.error('Database not found! Run: python scripts/generate_data.py then python scripts/clean_data.py')
        st.stop()
    conn = sqlite3.connect(str(DB_PATH))
    df = pd.read_sql_query('SELECT * FROM trains', conn)
    conn.close()
    df['date'] = pd.to_datetime(df['date'])
    return df

df = load_data()

# Sidebar filters
st.sidebar.title('\U0001f686 Rail Analytics')
st.sidebar.markdown('---')
st.sidebar.subheader('\U0001f4c5 Date Range')
min_date = df['date'].min().date()
max_date = df['date'].max().date()
date_range = st.sidebar.date_input('Select date range', value=(min_date, max_date), min_value=min_date, max_value=max_date, key='date_range')
if isinstance(date_range, tuple) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

st.sidebar.subheader('\U0001f682 Train Type')
train_types = ['All'] + sorted(df['train_type'].unique().tolist())
selected_type = st.sidebar.selectbox('Train type', train_types)

st.sidebar.subheader('\U0001f6e4 Route')
all_routes = sorted(df['route'].unique().tolist())
selected_routes = st.sidebar.multiselect('Select routes', all_routes, default=[], help='Leave empty for all')

st.sidebar.subheader('\U0001f326 Season')
seasons = ['All'] + sorted(df['season'].unique().tolist())
selected_season = st.sidebar.selectbox('Season', seasons)
st.sidebar.markdown('---')
st.sidebar.info(f'Dataset: {len(df):,} records')

# Apply filters
fd = df.copy()
fd = fd[(fd['date'].dt.date >= start_date) & (fd['date'].dt.date <= end_date)]
if selected_type != 'All': fd = fd[fd['train_type'] == selected_type]
if selected_routes: fd = fd[fd['route'].isin(selected_routes)]
if selected_season != 'All': fd = fd[fd['season'] == selected_season]

st.title('\U0001f686 Indian Railways Analytics Dashboard')
st.markdown('*Real-time insights into train performance, delays, and routes*')
st.markdown('---')

# KPI Cards
tt = len(fd)
ad = fd['delay_minutes'].mean() if tt else 0
otc = (fd['delay_minutes'] <= 5).sum()
otp = (otc / tt * 100) if tt else 0
tr = fd['route'].nunique()
c1,c2,c3,c4 = st.columns(4)
with c1: st.markdown(f'<div class="kpi-card"><h3>{tt:,}</h3><p>Total Trains</p></div>', unsafe_allow_html=True)
with c2: st.markdown(f'<div class="kpi-card orange"><h3>{ad:.1f} min</h3><p>Avg Delay</p></div>', unsafe_allow_html=True)
with c3: st.markdown(f'<div class="kpi-card green"><h3>{otp:.1f}%</h3><p>On-Time Performance</p></div>', unsafe_allow_html=True)
with c4: st.markdown(f'<div class="kpi-card blue"><h3>{tr}</h3><p>Active Routes</p></div>', unsafe_allow_html=True)
st.markdown('---')

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(['\U0001f4c8 Delay Trends', '\U0001f4ca Route Analysis', '\U0001f967 Distribution', '\U0001f525 Seasonal Heatmap'])

with tab1:
    st.subheader('Monthly Delay Trend')
    monthly = fd.groupby('year_month').agg(avg_delay=('delay_minutes','mean'), total_trains=('train_number','count'), major_delays=('delay_category', lambda x: (x=='Major Delay').sum())).reset_index().sort_values('year_month')
    if not monthly.empty:
        fig = px.line(monthly, x='year_month', y='avg_delay', markers=True, title='Average Delay by Month', labels={'year_month':'Month','avg_delay':'Avg Delay (min)'}, color_discrete_sequence=['#636EFA'])
        fig.update_layout(hovermode='x unified', xaxis_tickangle=-45, height=450)
        st.plotly_chart(fig, use_container_width=True)
        fig2 = px.bar(monthly, x='year_month', y='total_trains', title='Train Volume by Month', labels={'year_month':'Month','total_trains':'Number of Trains'}, color_discrete_sequence=['#00CC96'])
        fig2.update_layout(xaxis_tickangle=-45, height=350)
        st.plotly_chart(fig2, use_container_width=True)
    else: st.info('No data for selected filters.')

with tab2:
    st.subheader('Top 15 Most Delayed Routes')
    rs = fd.groupby('route').agg(avg_delay=('delay_minutes','mean'), train_count=('train_number','count')).reset_index()
    rs = rs[rs['train_count'] >= 3]
    td = rs.nlargest(15, 'avg_delay')
    if not td.empty:
        fig = px.bar(td, x='avg_delay', y='route', orientation='h', title='Top 15 Routes by Average Delay', labels={'avg_delay':'Avg Delay (min)','route':'Route'}, color='avg_delay', color_continuous_scale='RdYlGn_r', height=500)
        fig.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig, use_container_width=True)
        st.subheader('Top 15 Busiest Routes')
        bu = rs.nlargest(15, 'train_count')
        fig2 = px.bar(bu, x='train_count', y='route', orientation='h', title='Top 15 Routes by Train Frequency', labels={'train_count':'Number of Trains','route':'Route'}, color='train_count', color_continuous_scale='Blues', height=500)
        fig2.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig2, use_container_width=True)
    else: st.info('Not enough data for route analysis.')

with tab3:
    ca, cb = st.columns(2)
    with ca:
        st.subheader('Train Type Distribution')
        tc = fd['train_type'].value_counts().reset_index(); tc.columns = ['train_type','count']
        if not tc.empty:
            fig = px.pie(tc, values='count', names='train_type', title='Distribution by Train Type', hole=0.4, color_discrete_sequence=px.colors.qualitative.Set2)
            fig.update_traces(textposition='inside', textinfo='label+percent+value')
            st.plotly_chart(fig, use_container_width=True)
    with cb:
        st.subheader('Delay Category Breakdown')
        cc = fd['delay_category'].value_counts().reset_index(); cc.columns = ['delay_category','count']
        if not cc.empty:
            cmap = {'On-Time':'#00CC96','Minor Delay':'#FFA15A','Major Delay':'#EF553B'}
            fig = px.pie(cc, values='count', names='delay_category', title='Delay Category Distribution', hole=0.4, color='delay_category', color_discrete_map=cmap)
            fig.update_traces(textposition='inside', textinfo='label+percent+value')
            st.plotly_chart(fig, use_container_width=True)
    st.subheader('Delay Distribution')
    if not fd.empty:
        fig = px.histogram(fd, x='delay_minutes', nbins=40, title='Distribution of Delay Minutes', labels={'delay_minutes':'Delay (minutes)','count':'Frequency'}, color_discrete_sequence=['#AB63FA'])
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

with tab4:
    st.subheader('Seasonal Delay Heatmap')
    day_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    season_order = ['Winter','Summer','Monsoon','Post-Monsoon']
    hdata = fd.groupby(['season','day_of_week'])['delay_minutes'].mean().reset_index()
    if not hdata.empty:
        pivot = hdata.pivot(index='season', columns='day_of_week', values='delay_minutes')
        pivot = pivot.reindex(index=[s for s in season_order if s in pivot.index], columns=[d for d in day_order if d in pivot.columns])
        fig = px.imshow(pivot, title='Average Delay by Season & Day of Week', labels={'x':'Day of Week','y':'Season','color':'Avg Delay (min)'}, color_continuous_scale='YlOrRd', aspect='auto', height=400)
        fig.update_layout(xaxis={'side':'bottom'})
        st.plotly_chart(fig, use_container_width=True)
    st.subheader('Season-wise Performance')
    ss = fd.groupby('season').agg(avg_delay=('delay_minutes','mean'), on_time_pct=('delay_minutes', lambda x: (x<=5).sum()/len(x)*100 if len(x) else 0), total_trains=('train_number','count')).reset_index()
    if not ss.empty:
        ch1, ch2 = st.columns(2)
        with ch1:
            fig = px.bar(ss, x='season', y='avg_delay', title='Avg Delay by Season', labels={'season':'Season','avg_delay':'Avg Delay (min)'}, color='season', color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig, use_container_width=True)
        with ch2:
            fig = px.bar(ss, x='season', y='on_time_pct', title='On-Time % by Season', labels={'season':'Season','on_time_pct':'On-Time (%)'}, color='season', color_discrete_sequence=px.colors.qualitative.Pastel)
            st.plotly_chart(fig, use_container_width=True)
    st.subheader('Day of Week Analysis')
    dow = fd.groupby('day_of_week').agg(avg_delay=('delay_minutes','mean'), total=('train_number','count')).reset_index()
    dow['day_of_week'] = pd.Categorical(dow['day_of_week'], categories=day_order, ordered=True)
    dow = dow.sort_values('day_of_week')
    if not dow.empty:
        fig = px.bar(dow, x='day_of_week', y='avg_delay', title='Average Delay by Day of Week', labels={'day_of_week':'Day','avg_delay':'Avg Delay (min)'}, color='avg_delay', color_continuous_scale='Tealrose')
        st.plotly_chart(fig, use_container_width=True)

# Data table
st.markdown('---')
st.subheader('\U0001f4cb Data Explorer')
search = st.text_input('\U0001f50d Search trains (by name, number, station, or route)', placeholder='e.g., Rajdhani, New Delhi, 12345...')
tdf = fd.copy()
if search:
    mask = (tdf['train_name'].str.contains(search,case=False,na=False) | tdf['train_number'].str.contains(search,case=False,na=False) | tdf['source_station'].str.contains(search,case=False,na=False) | tdf['destination_station'].str.contains(search,case=False,na=False) | tdf['route'].str.contains(search,case=False,na=False))
    tdf = tdf[mask]
dc = ['train_number','train_name','source_station','destination_station','route','scheduled_departure','actual_departure','delay_minutes','delay_category','train_type','date','season']
st.caption(f'Showing {len(tdf):,} records')
st.dataframe(tdf[dc].reset_index(drop=True), use_container_width=True, height=500, hide_index=True)
st.download_button(label='\U0001f4e5 Download filtered data as CSV', data=tdf[dc].to_csv(index=False).encode('utf-8'), file_name='railway_data_filtered.csv', mime='text/csv')
st.markdown('---')
st.markdown('<div style="text-align:center;color:gray;font-size:0.85rem;">Indian Railways Analytics Dashboard &bull; Synthetic Data &bull; Built with Streamlit &amp; Plotly</div>', unsafe_allow_html=True)
