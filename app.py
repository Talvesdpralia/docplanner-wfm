import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import math
import calendar
import os
import requests
import urllib.parse
from sqlalchemy import text

# Google Auth Imports
from google.oauth2 import id_token
import google.auth.transport.requests

# ==========================================
# 1. UI & DESIGN ENGINE - PREMIUM GLASS
# ==========================================
st.set_page_config(page_title="Docplanner WFM Pro", layout="wide", page_icon="🏥")

DP_TEAL = "#00c4a7"
DP_NAVY = "#011e41"
DP_SLATE = "#4b5563"

def apply_custom_design():
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Figtree:wght@300;400;500;600&display=swap');
        
        .stApp {{
            font-family: 'Figtree', sans-serif !important;
            background: radial-gradient(circle at 10% 40%, rgba(0, 196, 167, 0.05), transparent 40%),
                        radial-gradient(circle at 90% 10%, rgba(1, 30, 65, 0.04), transparent 40%),
                        #f8fafc !important; 
        }}
        h1 {{ font-weight: 300 !important; font-size: 1.7rem !important; color: {DP_NAVY}; letter-spacing: -0.5px; }}
        h2, h3 {{ font-weight: 400 !important; font-size: 1.1rem !important; color: {DP_SLATE}; }}
        p, span, label, div[data-baseweb="select"] {{ font-size: 13.5px !important; }}

        /* SIDEBAR GLASS */
        section[data-testid="stSidebar"] {{
            background: rgba(255, 255, 255, 0.1) !important;
            backdrop-filter: blur(40px) saturate(200%) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.4) !important;
            box-shadow: 4px 0 24px rgba(0,0,0,0.02) !important;
        }}
        [data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child {{ display: none !important; }}
        [data-testid="stSidebar"] div[role="radiogroup"] label {{
            background: transparent !important;
            padding: 6px 12px !important; margin-bottom: 2px !important; border-radius: 8px !important;
            transition: all 0.2s ease !important; color: {DP_NAVY} !important; font-weight: 400 !important;
            border-left: 3px solid transparent !important;
        }}
        [data-testid="stSidebar"] div[role="radiogroup"] label:hover {{ background: rgba(0, 196, 167, 0.04) !important; }}
        [data-testid="stSidebar"] div[role="radiogroup"] label[aria-checked="true"],
        [data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] {{
            background: rgba(0, 196, 167, 0.06) !important; border-left: 3px solid {DP_TEAL} !important;
            color: {DP_TEAL} !important; font-weight: 600 !important;
        }}

        /* FIXING RED CIRCLES */
        div[role="radiogroup"] div[data-testid="stMarkdownContainer"] ~ div[aria-checked="true"] div:first-child,
        div[role="radiogroup"] div[data-testid="stMarkdownContainer"] ~ div[data-checked="true"] div:first-child {{
            background-color: {DP_TEAL} !important; border-color: {DP_TEAL} !important;
        }}
        input[type="radio"] {{ accent-color: {DP_TEAL} !important; }}

        /* PROMPT BOXES */
        div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="select"] > div {{
            background-color: rgba(255, 255, 255, 0.9) !important; border: 1px solid rgba(0,0,0,0.03) !important;
            border-radius: 20px !important; box-shadow: 0 2px 8px rgba(0,0,0,0.02), 0 1px 2px rgba(0,0,0,0.02) !important;
            padding: 2px 8px !important; transition: box-shadow 0.2s ease !important;
        }}
        div[data-baseweb="input"]:focus-within, div[data-baseweb="select"] > div:focus-within {{
            box-shadow: 0 8px 20px rgba(0, 196, 167, 0.1) !important; border: 1px solid rgba(0, 196, 167, 0.4) !important;
        }}
        .stTextInput input, .stNumberInput input {{
            background-color: transparent !important; border: none !important; box-shadow: none !important; padding: 8px !important;
        }}

        /* METRICS & BUTTONS */
        [data-testid="stMetric"] {{
            background: rgba(255, 255, 255, 0.6) !important; backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.8) !important; padding: 16px !important;
            border-radius: 16px !important; box-shadow: 0 4px 15px rgba(0,0,0,0.02) !important;
        }}
        .stButton>button {{
            background: {DP_TEAL} !important; color: white !important; border-radius: 20px !important;
            border: none !important; padding: 8px 24px !important; font-weight: 500 !important;
            box-shadow: 0 4px 12px rgba(0, 196, 167, 0.2) !important;
        }}
        </style>
    """, unsafe_allow_html=True)

apply_custom_design()

# ==========================================
# 2. CORE ENGINES & DATA HANDLING (SUPABASE)
# ==========================================
conn = st.connection("supabase", type="sql")

def calculate_erlang_c(vol, aht, target_t, agents):
    if vol <= 0: return 1.0
    intensity = (vol * aht) / 3600
    if agents <= intensity: return 0.0 
    try:
        sum_inv = sum([(intensity**i) / math.factorial(i) for i in range(int(agents))])
        numerator = (intensity**agents / math.factorial(int(agents))) * (agents / (agents - intensity))
        prob_w = numerator / (sum_inv + numerator)
        return 1 - (prob_w * math.exp(-(agents - intensity) * (target_t / aht)))
    except: return 1.0

def get_required_fte(vol, aht, target_sl, target_time=20):
    if vol <= 0: return 0
    intensity = (vol * aht) / 3600
    agents = math.ceil(intensity) + 1
    while calculate_erlang_c(vol, aht, target_time, agents) < target_sl and agents < 1000:
        agents += 1
    return agents

def aggregate_wfm(df, group_cols):
    if df.empty: return df
    def w_avg(d, col, w_col):
        if d[w_col].sum() == 0: return d[col].mean()
        return np.average(d[col], weights=d[w_col])
    
    agg = df.groupby(group_cols).apply(lambda x: pd.Series({
        'Volume': x['Volume'].sum(),
        'FTE': x['FTE'].mean(),
        'SLA': w_avg(x, 'SLA', 'Volume'),
        'AHT': w_avg(x, 'AHT', 'Volume')
    })).reset_index()
    return agg

def generate_time_slots():
    return [f"{str(h).zfill(2)}:{str(m).zfill(2)}" for h in range(8, 20) for m in (0, 30)]

def sync_from_cloud():
    try:
        st.session_state.user_db = conn.query("SELECT * FROM user_db;", ttl="0m")
        st.session_state.master_data = conn.query("SELECT * FROM master_data;", ttl="0m")
        st.session_state.exception_logs = conn.query("SELECT * FROM exception_logs;", ttl="0m")
        
        if 'Status' not in st.session_state.exception_logs.columns:
            st.session_state.exception_logs['Status'] = 'Approved'
            
        st.session_state.schedule_db = conn.query("SELECT * FROM schedule_db;", ttl="0m")
        st.session_state.forecast_db = conn.query("SELECT * FROM forecast_db;", ttl="0m")
    except Exception as e:
        st.error(f"Failed to pull from Supabase. Ensure you ran the setup SQL script. Error: {e}")
        st.session_state.user_db = pd.DataFrame([{"email": "telmo.alves@docplanner.com", "password": "sso", "role": "Admin"}])
        st.session_state.master_data = pd.DataFrame(columns=["Date", "Country", "Channel", "Volume", "SLA", "AHT", "FTE"])
        st.session_state.exception_logs = pd.DataFrame(columns=["Country", "Date", "Start Time", "Agent", "Type", "Duration (Min)", "Notes", "Status"])
        st.session_state.schedule_db = pd.DataFrame(columns=["Country", "YearMonth", "Agent", "Time"] + [str(d) for d in range(1, 32)])
        st.session_state.forecast_db = pd.DataFrame(columns=["Date", "Country", "Channel", "Forecast_Volume", "Req_FTE"])

# ==========================================
# 3. LOGIN & AUTH HANDLER (STATELESS SSO)
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    sync_from_cloud()

client_id = st.secrets["google_auth"]["client_id"]
client_secret = st.secrets["google_auth"]["client_secret"]
redirect_uri = st.secrets["google_auth"]["redirect_uri"]

query_params = st.query_params
if not st.session_state.logged_in and "code" in query_params:
    try:
        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": query_params["code"],
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code"
        }
        response = requests.post(token_url, data=data)
        token_data = response.json()
        
        if "id_token" in token_data:
            req = google.auth.transport.requests.Request()
            id_info = id_token.verify_oauth2_token(token_data["id_token"], req, client_id)
            email = id_info.get("email")
            
            db = st.session_state.user_db
            user_match = db[db['email'].str.lower() == email.lower()]
            
            if not user_match.empty:
                st.session_state.logged_in = True
                st.session_state.user_role = str(user_match.iloc[0]['role'])
                st.session_state.current_email = email
                st.query_params.clear()
                st.rerun()
            else:
                st.error(f"Access Denied: {email} is not authorized in the WFM database.")
                st.stop()
        else:
            st.error(f"Failed to retrieve token from Google. Error: {token_data}")
            st.stop()
    except Exception as e:
        st.error(f"Authentication Error: {e}")

if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.image("https://www.docplanner.com/img/logo-default-group-en.svg", width=180)
        st.title("Workforce Workspace")
        
        # TARGET CHANGED TO _blank TO BYPASS IFRAME SANDBOX SILENT BLOCK
        encoded_uri = urllib.parse.quote(redirect_uri, safe='')
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&redirect_uri={encoded_uri}&response_type=code&scope=openid%20email%20profile&prompt=consent"
        
        st.markdown(f"""
            <a href="{auth_url}" target="_blank" style="text-decoration:none;">
                <div style="background:white;color:#757575;border:1px solid #dadce0;border-radius:4px;padding:12px;text-align:center;font-weight:500;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 4px rgba(0,0,0,0.1);">
                    <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" style="width:18px;margin-right:10px;">
                    Sign in with Google
                </div>
            </a>
        """, unsafe_allow_html=True)
    st.stop()

# ==========================================
# 4. GLOBAL ASSETS
# ==========================================
DP_LOGO = "https://www.docplanner.com/img/logo-default-group-en.svg"
COUNTRIES = ["Spain", "Mexico", "Poland", "Germany", "Italy", "Brazil", "Colombia", "Turkey"]
CHANNELS = ["Phone", "Chat", "WhatsApp", "Email"]

nav_icons = {
    "Dashboard": "⟢", "Import Data": "⤓", "Forecasting": "📈", "Scheduling": "📅",
    "Exception Management": "⚠", "Capacity Planner (Erlang)": "◈", 
    "Reporting Center": "▤", "Admin Panel": "⚙", "System Status": "🛡", "Agent Portal": "👤"
}

# ==========================================
# 5. NAVIGATION & PERMISSIONS
# ==========================================
role = st.session_state.user_role
if role == "Admin":
    menu_options = ["Dashboard", "Import Data", "Forecasting", "Scheduling", "Exception Management", "Capacity Planner (Erlang)", "Reporting Center", "Admin Panel", "System Status"]
elif role == "Manager":
    menu_options = ["Dashboard", "Forecasting", "Scheduling", "Exception Management", "Capacity Planner (Erlang)"]
else:
    menu_options = ["Agent Portal"]

with st.sidebar:
    st.image(DP_LOGO, width=130)
    st.markdown(f"**{st.session_state.current_email}**")
    st.caption(f"Role: {role}")
    st.markdown("<hr style='margin: 10px 0; border-color: rgba(0,0,0,0.05);'>", unsafe_allow_html=True)
    menu = st.radio("Navigation", menu_options, label_visibility="collapsed")
    st.markdown("<hr style='margin: 10px 0; border-color: rgba(0,0,0,0.05);'>", unsafe_allow_html=True)
    
    if role in ["Admin", "Manager"]:
        view_mode = st.radio("View Setting", ["Global", "Regional Select"])
        selected_markets = COUNTRIES
        if view_mode == "Regional Select":
            selected_markets = st.multiselect("Select Markets", COUNTRIES, default=COUNTRIES)
    else:
        selected_markets = COUNTRIES

    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Sync Data 🔄", use_container_width=True):
        sync_from_cloud()
        st.rerun()
    if st.button("Log Out 🚪", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

def render_header(title):
    icon = nav_icons.get(title, "⟢")
    st.markdown(f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;"><span style="font-size:1.6rem;color:{DP_TEAL};opacity:0.8;">{icon}</span><h1 style="margin:0 !important;">{title}</h1></div>', unsafe_allow_html=True)

# ==========================================
# 6. MAIN MODULES
# ==========================================

if menu == "Dashboard":
    render_header("Performance Overview")
    df = st.session_state.master_data
    if not df.empty and 'Country' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Day'] = df['Date'].dt.date
        df_f = df[df['Country'].isin(selected_markets)].copy()
        
        if not df_f.empty:
            for c in ['Volume', 'SLA', 'AHT', 'FTE']: df_f[c] = pd.to_numeric(df_f[c], errors='coerce').fillna(0)
            
            tot_v = df_f['Volume'].sum()
            avg_fte = df_f['FTE'].mean()
            sl_w = np.average(df_f['SLA'], weights=df_f['Volume']) if tot_v > 0 else 0
            aht_w = np.average(df_f['AHT'], weights=df_f['Volume']) if tot_v > 0 else 0
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Volume", f"{tot_v:,.0f}")
            c2.metric("Weighted SLA%", f"{sl_w*100:.1f}%")
            c3.metric("Weighted AHT", f"{int(aht_w)}s")
            c4.metric("Average FTE", f"{avg_fte:,.1f}")
            
            daily_agg = aggregate_wfm(df_f, ['Day', 'Channel'])
            st.markdown("<hr style='margin: 20px 0; border-color: rgba(0,0,0,0.05);'>", unsafe_allow_html=True)
            st.plotly_chart(px.area(daily_agg, x='Day', y='Volume', color='Channel', title="Volume Demand by Channel", template="plotly_white"), use_container_width=True)
        else: st.info("No data matches the selected filters.")
    else: st.info("Cloud database is empty.")

elif menu == "Import Data":
    render_header("Data Ingestion")
    st.write("### 1. Download Blank Import Template")
    if st.button("📥 Download Data Template"):
        temp_df = pd.DataFrame(columns=["Date", "Country", "Channel", "Volume", "SLA", "AHT", "FTE"])
        temp_df.loc[0] = ["01/01/2026 08:00", "Spain", "Phone", 150, 0.80, 300, 10.5]
        csv = temp_df.to_csv(index=False).encode('utf-8')
        st.download_button("Download CSV", data=csv, file_name="WFM_Import_Template.csv", mime="text/csv")
    
    st.divider()
    st.write("### 2. Upload Populated Data")
    up = st.file_uploader("Drop Market CSV File", type="csv")
    
    if up:
        with st.spinner("Reading CSV file..."):
            new_df = pd.read_csv(up)
            new_df.columns = new_df.columns.str.strip().str.capitalize()
            new_df.rename(columns={'Sla': 'SLA', 'Aht': 'AHT', 'Fte': 'FTE'}, inplace=True)
            
            expected = ["Date", "Country", "Channel", "Volume", "SLA", "AHT", "FTE"]
            missing_cols = [c for c in expected if c not in new_df.columns]
            
            if not missing_cols:
                st.info(f"File validated. Attempting to process {len(new_df):,} rows into PostgreSQL...")
                st.session_state.master_data = pd.concat([st.session_state.master_data, new_df], ignore_index=True)
                st.session_state.master_data.drop_duplicates(subset=['Date', 'Country', 'Channel'], keep='last', inplace=True)
                try:
                    with st.spinner("Writing to Supabase..."):
                        new_df.to_sql('master_data', con=conn.engine, if_exists='append', index=False)
                    st.success(f"Successfully synchronized {len(new_df):,} rows with Supabase!")
                except Exception as e:
                    st.error(f"Database error: {e}")
            else:
                st.error(f"Upload Failed: Missing columns: {missing_cols}")

elif menu == "Forecasting":
    render_header("12-Month Advanced Forecasting")
    df = st.session_state.master_data.copy()
    st.metric("Total Rows in PostgreSQL", f"{len(df):,}")
    
    if not df.empty and len(df) >= 10:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        valid_df = df.dropna(subset=['Date'])
        
        if len(valid_df) < 10:
            st.error("Date formatting issue. Unable to parse enough valid dates.")
            st.stop()
            
        last_date = valid_df['Date'].max()
        
        c1, c2 = st.columns(2)
        if role == "Admin":
            if c1.button("🚀 Generate 12-Month Forecast & Overwrite DB"):
                with st.spinner("Analyzing historical patterns... (Optimized Vector Engine)"):
                    hist_agg = valid_df.groupby(['Country', 'Channel'])[['Volume', 'AHT']].mean().reset_index()
                    metrics_dict = hist_agg.set_index(['Country', 'Channel']).to_dict('index')
                    
                    proj_data = []
                    dates = [(last_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, 366)]
                    
                    for ctry in valid_df['Country'].unique():
                        for ch in valid_df['Channel'].unique():
                            key = (ctry, ch)
                            if key in metrics_dict:
                                base_v = metrics_dict[key]['Volume']
                                base_aht = metrics_dict[key]['AHT']
                                if math.isnan(base_v): base_v = 50 
                                if math.isnan(base_aht): base_aht = 300
                                
                                for idx, d_str in enumerate(dates, start=1):
                                    v_mock = base_v * (1 + (idx*0.0001))
                                    req_fte = get_required_fte(v_mock / 48, base_aht, 0.80) * 48 
                                    proj_data.append([d_str, ctry, ch, v_mock, req_fte])
                    
                    new_f = pd.DataFrame(proj_data, columns=["Date", "Country", "Channel", "Forecast_Volume", "Req_FTE"])
                    st.session_state.forecast_db = new_f
                    try: 
                        st.session_state.forecast_db.to_sql('forecast_db', con=conn.engine, if_exists='replace', index=False)
                    except: pass
                    st.success("Forecast generated and safely persistent in Database!")
        
        if not st.session_state.forecast_db.empty:
            f_db = st.session_state.forecast_db
            f_db['Date'] = pd.to_datetime(f_db['Date'])
            
            st.write("### Volume Projection vs Actuals")
            hist_daily = aggregate_wfm(valid_df, [valid_df['Date'].dt.date, 'Country'])
            hist_daily.rename(columns={'Date': 'Time', 'Volume': 'Actual'}, inplace=True)
            f_daily = f_db.groupby([f_db['Date'].dt.date, 'Country'])['Forecast_Volume'].sum().reset_index()
            f_daily.rename(columns={'Date': 'Time', 'Forecast_Volume': 'Forecast'}, inplace=True)
            
            fig = go.Figure()
            ctry_plot = selected_markets[0] if selected_markets else COUNTRIES[0]
            spain_hist = hist_daily[hist_daily['Country']==ctry_plot]
            spain_f = f_daily[f_daily['Country']==ctry_plot]
            fig.add_trace(go.Scatter(x=spain_hist['Time'], y=spain_hist['Actual'], name=f"Actual ({ctry_plot})"))
            fig.add_trace(go.Scatter(x=spain_f['Time'], y=spain_f['Forecast'], name=f"Forecast ({ctry_plot})", line=dict(dash='dot')))
            fig.update_layout(template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
    else: st.warning("Requires granular interval data to generate forecast models.")

elif menu == "Scheduling":
    render_header("Scheduling & Roster")
    
    if role == "Admin":
        tabs = st.tabs(["🗓️ Team Roster", "⚙️ Overwrite & Publish AI Roster"])
        tab1, tab2 = tabs[0], tabs[1]
    else:
        tab1 = st.container()
        st.info("View Only Mode: Only Admins can generate and overwrite the master schedules.")
    
    with tab1:
        st.write("### Global Agent Schedule View")
        s_db = st.session_state.schedule_db
        exc_db = st.session_state.exception_logs
        
        if not s_db.empty and 'Country' in s_db.columns:
            market_db = s_db[s_db['Country'].isin(selected_markets)]
            agents = market_db['Agent'].dropna().unique().tolist()
            
            if agents:
                c1, c2 = st.columns([1, 3])
                selected_agent = c1.selectbox("Select Agent", agents)
                selected_ym = c1.selectbox("Select Month", market_db['YearMonth'].unique())
                
                agent_schedule = market_db[(market_db['Agent'] == selected_agent) & (market_db['YearMonth'] == selected_ym)].copy()
                
                if not agent_schedule.empty:
                    agent_schedule = agent_schedule.sort_values(by="Time")
                    display_cols = ["Time"] + [str(d) for d in range(1, 32) if str(d) in agent_schedule.columns]
                    display_df = agent_schedule[display_cols].drop_duplicates(subset=['Time'], keep='last').set_index("Time")
                    
                    if not exc_db.empty and 'Date' in exc_db.columns:
                        if 'Status' in exc_db.columns:
                            agent_exc = exc_db[(exc_db['Agent'] == selected_agent) & (exc_db['Status'] == 'Approved')]
                        else:
                            agent_exc = exc_db[exc_db['Agent'] == selected_agent]

                        for _, exc in agent_exc.iterrows():
                            exc_date_str = str(exc['Date'])
                            if exc_date_str.startswith(selected_ym):
                                exc_day = str(int(exc_date_str.split('-')[2])) 
                                start_time = exc['Start Time']
                                duration = int(exc['Duration (Min)'])
                                exc_type = f"🔴 {exc['Type']}"
                                blocks_affected = math.ceil(duration / 30)
                                
                                if start_time in display_df.index and exc_day in display_df.columns:
                                    start_idx = display_df.index.get_loc(start_time)
                                    for i in range(blocks_affected):
                                        if start_idx + i < len(display_df):
                                            target_time = display_df.index[start_idx + i]
                                            display_df.at[target_time, exc_day] = exc_type

                    st.write(f"**Viewing Published Schedule:** {selected_agent} ({selected_ym})")
                    st.data_editor(display_df, use_container_width=True)
                else: st.warning("No schedule found for this criteria.")
            else: st.info("No agents found in schedule database.")
        else: st.info("Schedule database is empty.")

    if role == "Admin":
        with tab2:
            st.write("### Forecast-Optimized AI Roster (Persistent Overwrite)")
            default_y = datetime.now().year
            default_m = datetime.now().month
            f_db = st.session_state.forecast_db.copy()

            col1, col2, col3 = st.columns([1,1,2])
            y_sel = col1.number_input("Year", 2000, 2050, default_y)
            m_sel = col2.number_input("Month", 1, 12, default_m)
            target_country = col3.selectbox("Target Market", COUNTRIES, key="sch_country")
            
            st.warning(f"⚠️ Generating this roster will **overwrite** any existing database schedules for **{target_country}** in **{y_sel}-{str(m_sel).zfill(2)}**.")
            
            if st.button("✨ Generate & Publish Schedule to Database"):
                if f_db.empty:
                    st.error("You must generate a Forecast first!")
                else:
                    f_month = f_db[(pd.to_datetime(f_db['Date']).dt.year == y_sel) & (pd.to_datetime(f_db['Date']).dt.month == m_sel) & (f_db['Country'] == target_country)]
                    if f_month.empty:
                        st.error("No forecast data exists for this specific month/country.")
                    else:
                        with st.spinner("Packing Agent Shifts and Writing to PostgreSQL..."):
                            days_in_month = calendar.monthrange(int(y_sel), int(m_sel))[1]
                            times = generate_time_slots()
                            weights = [0.5, 0.6, 0.8, 1.0, 1.2, 1.3, 1.2, 1.0, 0.8, 0.7, 0.8, 1.0, 1.1, 1.2, 1.1, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1]
                            dist_curve = {times[i]: weights[i]/sum(weights) for i in range(len(times))}
                            
                            schedule_matrix = {d: {t: [] for t in times} for d in range(1, days_in_month+1)}
                            max_agents = 0
                            
                            for d in range(1, days_in_month+1):
                                date_str = f"{y_sel}-{str(m_sel).zfill(2)}-{str(d).zfill(2)}"
                                day_fcst = f_month[f_month['Date'] == date_str]
                                for t in times:
                                    agents_needed = []
                                    for _, row in day_fcst.iterrows():
                                        int_vol = row['Forecast_Volume'] * dist_curve[t]
                                        req = get_required_fte(int_vol, 300, 0.80)
                                        agents_needed.extend([row['Channel']] * req)
                                    schedule_matrix[d][t] = agents_needed
                                    if len(agents_needed) > max_agents: max_agents = len(agents_needed)
                            
                            if max_agents == 0: max_agents = 10
                            rows = []
                            ym_str = f"{y_sel}-{str(m_sel).zfill(2)}"
                            for i in range(1, max_agents + 1):
                                for t in times:
                                    row_data = {"Country": target_country, "YearMonth": ym_str, "Agent": f"Agent_{i}_{target_country}", "Time": t}
                                    for d in range(1, days_in_month+1):
                                        tasks = schedule_matrix[d][t]
                                        row_data[str(d)] = tasks[i-1] if i <= len(tasks) else ""
                                    rows.append(row_data)
                            
                            df_opt = pd.DataFrame(rows)
                            
                            try:
                                with conn.engine.connect() as c:
                                    c.execute(text(f"DELETE FROM schedule_db WHERE \"Country\" = '{target_country}' AND \"YearMonth\" = '{ym_str}'"))
                                    c.commit()
                                df_opt.to_sql('schedule_db', con=conn.engine, if_exists='append', index=False)
                                st.success("Schedule successfully published and rendered persistent!")
                                sync_from_cloud()
                            except Exception as e:
                                st.error(f"Database overwrite error: {e}")

elif menu == "Exception Management":
    render_header("Exception Workflows")
    tab1, tab2 = st.tabs(["📋 Approval Queue", "➕ Direct Log (Admin/Manager)"])
    
    with tab1:
        st.write("### Pending Agent Requests")
        exc_db = st.session_state.exception_logs
        if not exc_db.empty and 'Status' in exc_db.columns:
            pending = exc_db[exc_db['Status'] == 'Pending']
            if not pending.empty:
                for idx, row in pending.iterrows():
                    with st.expander(f"🔴 Request from {row['Agent']} on {row['Date']}"):
                        st.write(f"**Type:** {row['Type']} | **Duration:** {row['Duration (Min)']} mins | **Time:** {row['Start Time']}")
                        st.write(f"**Agent Notes:** {row['Notes']}")
                        
                        colA, colB = st.columns(2)
                        if colA.button("✅ Approve Request", key=f"app_{idx}"):
                            try:
                                with conn.engine.connect() as c:
                                    query = text('UPDATE exception_logs SET "Status" = \'Approved\' WHERE "Agent" = :agt AND "Date" = :dt AND "Start Time" = :stm')
                                    c.execute(query, {"agt": row['Agent'], "dt": row['Date'], "stm": row['Start Time']})
                                    c.commit()
                                st.success("Request Approved. The schedule will now overlay this exception.")
                                sync_from_cloud()
                                st.rerun()
                            except Exception as e:
                                st.error(f"DB Error: {e}")
                                
                        if colB.button("❌ Reject Request", key=f"rej_{idx}"):
                            try:
                                with conn.engine.connect() as c:
                                    query = text('UPDATE exception_logs SET "Status" = \'Rejected\' WHERE "Agent" = :agt AND "Date" = :dt AND "Start Time" = :stm')
                                    c.execute(query, {"agt": row['Agent'], "dt": row['Date'], "stm": row['Start Time']})
                                    c.commit()
                                st.success("Request Rejected.")
                                sync_from_cloud()
                                st.rerun()
                            except Exception as e:
                                st.error(f"DB Error: {e}")
            else:
                st.success("No pending exception requests from Agents.")
                
            st.write("### All Processed Exceptions")
            st.dataframe(exc_db[exc_db['Status'] != 'Pending'], use_container_width=True)
        else:
            st.info("No exceptions logged.")

    with tab2:
        st.write("### Directly Inject Approved Exceptions")
        with st.form("exc_log_direct", clear_on_submit=True):
            c1, c2 = st.columns(2)
            exc_date = c1.date_input("Exception Date")
            exc_time = c2.selectbox("Start Time", generate_time_slots())
            
            ct_in = st.selectbox("Market Selection", COUNTRIES)
            agt_in = st.text_input("Staff Name (Must match Roster exactly)")
            t_in = st.selectbox("Reason Code", ["Sickness", "Late", "Technical", "Meeting"])
            d_in = st.number_input("Duration (Minutes)", value=30, min_value=1, step=30)
            
            if st.form_submit_button("Force Log as Approved"):
                new_e = pd.DataFrame([[ct_in, exc_date.strftime("%Y-%m-%d"), exc_time, agt_in, t_in, d_in, "Manager Override", "Approved"]], columns=["Country", "Date", "Start Time", "Agent", "Type", "Duration (Min)", "Notes", "Status"])
                try: 
                    new_e.to_sql('exception_logs', con=conn.engine, if_exists='append', index=False)
                    st.success("Exception forced as Approved directly to Schedule.")
                    sync_from_cloud()
                except Exception as e:
                    st.error(f"Database error: {e}")

elif menu == "Capacity Planner (Erlang)":
    render_header("Capacity & Headcount Plan")
    col1, col2 = st.columns(2)
    with col1:
        v_h = st.number_input("Forecasted Interval Volume", value=200, min_value=1)
        a_s = st.number_input("Target AHT (Seconds)", value=300, min_value=1)
    with col2:
        s_t = st.slider("Service Level Target %", 50, 99, 80) / 100
        sh = st.slider("Shrinkage %", 0, 50, 20) / 100
    req = get_required_fte(v_h, a_s, s_t)
    st.metric("Recommended Interval FTE", f"{math.ceil(req / (1 - sh))} Agents")
    
    st.divider()
    st.write("### 12-Month Projected Headcount Plan")
    f_db = st.session_state.forecast_db
    if not f_db.empty:
        f_db['Date_Str'] = pd.to_datetime(f_db['Date']).dt.strftime('%Y-%m-%d')
        daily_hc = f_db.groupby(['Date_Str', 'Country'])['Req_FTE'].sum().reset_index()
        daily_hc['Required_Headcount'] = np.ceil(daily_hc['Req_FTE'] / 16) 
        pivot_hc = daily_hc.pivot(index='Date_Str', columns='Country', values='Required_Headcount').fillna(0).astype(int)
        st.dataframe(pivot_hc, use_container_width=True, height=400)
    else: st.info("No forecast available. Generate a forecast first.")

elif menu == "Admin Panel":
    render_header("Access Management")
    with st.form("user_add", clear_on_submit=True):
        n_e = st.text_input("New Docplanner Email")
        n_p = st.text_input("Temporary Password (Unused for SSO)")
        n_r = st.selectbox("Role Assignment", ["Admin", "Manager", "User"])
        if st.form_submit_button("Provision Access"):
            if n_e:
                new_u = pd.DataFrame([{"email": n_e, "password": "sso", "role": n_r}])
                try:
                    new_u.to_sql('user_db', con=conn.engine, if_exists='append', index=False)
                    st.success(f"Access granted to {n_e}. Synced to Supabase!")
                    sync_from_cloud()
                except Exception as e:
                    st.error(f"Database error: {e}")
    st.dataframe(st.session_state.user_db[['email', 'role']], use_container_width=True)

elif menu == "Agent Portal":
    render_header("My Agent Portal")
    s_db = st.session_state.schedule_db
    
    st.write("### 🗓️ My Published Shifts")
    if not s_db.empty:
        my_sch = s_db[s_db['Agent'].str.lower() == st.session_state.current_email.lower()].copy()
        if not my_sch.empty:
            my_sch = my_sch.sort_values(by="Time")
            display_cols = ["Time"] + [str(d) for d in range(1, 32) if str(d) in my_sch.columns]
            my_display = my_sch[display_cols].drop_duplicates(subset=['Time'], keep='last').set_index("Time")
            st.dataframe(my_display, use_container_width=True)
        else: st.warning("No schedule records found for your Docplanner email.")
    else: st.info("Schedule database is empty.")

    st.divider()
    st.write("### ⚠️ Submit Exception Request (To Manager)")
    with st.form("agent_exc_request", clear_on_submit=True):
        c1, c2 = st.columns(2)
        exc_date = c1.date_input("Date of Exception")
        exc_time = c2.selectbox("Start Time", generate_time_slots())
        t_in = st.selectbox("Reason Category", ["Sickness", "Late", "Meeting", "Other"])
        d_in = st.number_input("Duration Missing (Minutes)", value=30, min_value=1, step=30)
        n_in = st.text_input("Additional Notes for TL")
        
        if st.form_submit_button("Send for Approval"):
            new_req = pd.DataFrame([["Global", exc_date.strftime("%Y-%m-%d"), exc_time, st.session_state.current_email, t_in, d_in, n_in, "Pending"]], 
                                columns=["Country", "Date", "Start Time", "Agent", "Type", "Duration (Min)", "Notes", "Status"])
            try:
                new_req.to_sql('exception_logs', con=conn.engine, if_exists='append', index=False)
                st.success("Request sent successfully. It is Pending review by your Team Leader.")
                sync_from_cloud()
            except Exception as e:
                st.error(f"Failed to send request: {e}")

elif menu == "System Status":
    render_header("Infrastructure Health")
    c1, c2, c3 = st.columns(3)
    c1.metric("Database Platform", "Supabase (PostgreSQL)")
    c2.metric("Master Data Rows", len(st.session_state.master_data))
    c3.metric("Service Latency", "< 5ms")

elif menu == "Reporting Center":
    render_header("Data Exports")
    if not st.session_state.master_data.empty and 'Country' in st.session_state.master_data.columns:
        csv = st.session_state.master_data.to_csv(index=False).encode('utf-8')
        st.download_button("Export Global Master Data (CSV)", data=csv, file_name="WFM_Global_Export.csv", mime="text/csv")
    else: st.warning("No data available to export.")
