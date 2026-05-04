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

STATUS_DICT = {
    "1:1": "For one on ones between managers and specialists.",
    "All Channels": "When managing all channels.",
    "Birthday": "Day off to celebrate birthday",
    "Parental Leave": "For leaves related to new borns.",
    "DPP Phone": "Exclusive to Poland. Agent working on DPP",
    "DPP Chat": "Exclusive to Poland. Agent working on DPP",
    "Phone & Cases": "When managing calls and cases.",
    "Cases": "When managing just cases.",
    "Chat": "When managing just chats.",
    "Chat & Cases": "When managing chat and cases.",
    "Chat & Whatsapp": "When managing chat and whatsapp.",
    "Whatsapp": "When managing whatsapp only.",
    "Holiday": "For approved holidays.",
    "Import": "Specific for Poland - Project of data import",
    "Language Class": "Time dedicated for language classes",
    "Lunch": "Exclusively for lunch time.",
    "Medical Appt": "For medical appointments or consults with doctors.",
    "Meeting": "For any type of meeting that requires the specialist to not be available to manage inbound or cases.",
    "Off": "For public holidays (region, city, country holidays) or other specific reasons where the agent won´t work",
    "Off queue": "When the specialist should be off queue but still working.",
    "Guardia_Off": "Specific for Mexico - Used to recover time made during Saturdays (Guardia)",
    "Outbound": "When dealing with outbound calls only",
    "Project": "Whenever a specialist will work on a project and wont be available to manage inbound or cases.",
    "Shadowing": "When doing shadowing.",
    "Sick Leave": "For sick leaves.",
    "TL Request": "Related to tasks asked by the Team Leaders",
    "Training": "For trainings.",
    "Triage and Cases": "During ramp up period but already managing cases."
}

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
        'FTE': x.get('FTE', pd.Series([0])).mean(),
        'SLA': w_avg(x, 'SLA', 'Volume') if 'SLA' in x.columns else 0.80,
        'AHT': w_avg(x, 'AHT', 'Volume') if 'AHT' in x.columns else 300
    })).reset_index()
    return agg

def generate_time_slots():
    return [f"{str(h).zfill(2)}:{str(m).zfill(2)}" for h in range(0, 24) for m in (0, 30)]

def sync_from_cloud():
    try:
        st.session_state.user_db = conn.query("SELECT * FROM user_db;", ttl="0m")
        
        # Load master_data and safely split Date and Time for the app's internal engines
        md = conn.query("SELECT * FROM master_data;", ttl="0m")
        if not md.empty and 'Date' in md.columns:
            dt_series = pd.to_datetime(md['Date'], errors='coerce')
            md['Time'] = dt_series.dt.strftime('%H:%M')
            md['Date'] = dt_series.dt.date.astype(str)
        st.session_state.master_data = md
        
        st.session_state.exception_logs = conn.query("SELECT * FROM exception_logs;", ttl="0m")
        
        if 'Status' not in st.session_state.exception_logs.columns:
            st.session_state.exception_logs['Status'] = 'Approved'
            
        st.session_state.schedule_db = conn.query("SELECT * FROM schedule_db;", ttl="0m")
        st.session_state.forecast_db = conn.query("SELECT * FROM forecast_db;", ttl="0m")
    except Exception as e:
        st.error(f"Failed to pull from Supabase. Ensure database tables exist. Error: {e}")
        st.session_state.user_db = pd.DataFrame([{"email": "telmo.alves@docplanner.com", "password": "sso", "role": "Admin"}])
        st.session_state.master_data = pd.DataFrame(columns=["Date", "Time", "Country", "Channel", "Volume", "SLA", "AHT", "FTE"])
        st.session_state.exception_logs = pd.DataFrame(columns=["Country", "Date", "Start Time", "Agent", "Type", "Duration (Min)", "Notes", "Status"])
        st.session_state.schedule_db = pd.DataFrame(columns=["Country", "YearMonth", "Date", "Time", "Agent", "Base_Activity"])
        st.session_state.forecast_db = pd.DataFrame(columns=["Date", "Time", "Country", "Channel", "Forecast_Volume", "Req_FTE"])

# ==========================================
# 3. LOGIN & AUTH HANDLER (STATELESS SSO)
# ==========================================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    sync_from_cloud()

client_id = st.secrets.get("google_auth", {}).get("client_id", "")
client_secret = st.secrets.get("google_auth", {}).get("client_secret", "")
redirect_uri = st.secrets.get("google_auth", {}).get("redirect_uri", "")

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
# 4. GLOBAL ASSETS & NAVIGATION
# ==========================================
DP_LOGO = "https://www.docplanner.com/img/logo-default-group-en.svg"
COUNTRIES = ["Spain", "Mexico", "Poland", "Germany", "Italy", "Brazil", "Colombia", "Turkey"]
CHANNELS = ["Phone", "Chat", "WhatsApp", "Email"]

nav_icons = {
    "Dashboard": "⟢", "Import Data": "⤓", "Forecasting": "📈", "Scheduling": "📅",
    "Exception Management": "⚠", "Capacity Planner (Erlang)": "◈", 
    "Reporting Center": "▤", "Admin Panel": "⚙", "System Status": "🛡", "Agent Portal": "👤",
    "Real-Time Ops": "📡"
}

role = st.session_state.user_role
if role == "Admin":
    menu_options = ["Dashboard", "Import Data", "Forecasting", "Scheduling", "Exception Management", "Capacity Planner (Erlang)", "Reporting Center", "Real-Time Ops", "Admin Panel", "System Status"]
elif role == "Manager":
    menu_options = ["Dashboard", "Forecasting", "Scheduling", "Exception Management", "Capacity Planner (Erlang)", "Real-Time Ops"]
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
# 5. MAIN MODULES
# ==========================================

if menu == "Dashboard":
    render_header("Performance Overview")
    df = st.session_state.master_data
    if not df.empty and 'Country' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df['Day'] = df['Date'].dt.date
        df_f = df[df['Country'].isin(selected_markets)].copy()
        
        if not df_f.empty:
            for c in ['Volume', 'SLA', 'AHT', 'FTE']: 
                if c in df_f.columns:
                    df_f[c] = pd.to_numeric(df_f[c], errors='coerce').fillna(0)
            
            tot_v = df_f['Volume'].sum() if 'Volume' in df_f.columns else 0
            avg_fte = df_f['FTE'].mean() if 'FTE' in df_f.columns else 0
            sl_w = np.average(df_f['SLA'], weights=df_f['Volume']) if 'SLA' in df_f.columns and tot_v > 0 else 0.80
            aht_w = np.average(df_f['AHT'], weights=df_f['Volume']) if 'AHT' in df_f.columns and tot_v > 0 else 300
            
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
    render_header("Data Ingestion & Aggregation")
    st.write("### 1. Upload Raw Historical Data (telmo_forecast_v1 format)")
    st.markdown("""
    The system will automatically parse the exact timestamps, aggregate them into 30-minute intervals, and convert `aht_minutes` into seconds for the Erlang-C model. It aligns perfectly with your Supabase schema.
    """)
    up = st.file_uploader("Drop Market CSV File", type="csv")
    
    if up:
        with st.spinner("Processing raw timestamps and aggregating into 30-min intervals..."):
            raw_df = pd.read_csv(up)
            
            required_cols = ['date_timestamp', 'country', 'channel', 'aht_minutes', 'case_id']
            missing_cols = [c for c in required_cols if c not in raw_df.columns]
            
            if not missing_cols:
                raw_df['date_timestamp'] = pd.to_datetime(raw_df['date_timestamp'], errors='coerce')
                raw_df = raw_df.dropna(subset=['date_timestamp'])
                
                # Floor exactly to 30-minute blocks and combine to the format expected by the DB
                raw_df['interval'] = raw_df['date_timestamp'].dt.floor('30min')
                raw_df['Date'] = raw_df['interval'].dt.strftime('%Y-%m-%d %H:%M:%S')
                
                agg_df = raw_df.groupby(['Date', 'country', 'channel']).agg(
                    Volume=('case_id', 'count'),
                    AHT=('aht_minutes', lambda x: x.mean() * 60) # Convert to seconds
                ).reset_index()
                
                agg_df.rename(columns={'country': 'Country', 'channel': 'Channel'}, inplace=True)
                
                # Assign defaults for SLA and FTE to match the Database definition
                agg_df['SLA'] = 0.80
                agg_df['FTE'] = 0.0
                
                st.write("### Aggregated 30-Min Intervals Ready for Database")
                st.dataframe(agg_df.head(10))
                
                if st.button("Commit to Supabase"):
                    try:
                        agg_df.to_sql('master_data', con=conn.engine, if_exists='append', index=False)
                        st.success(f"Successfully committed {len(agg_df)} interval records to Supabase!")
                        sync_from_cloud()
                    except Exception as e:
                        st.error(f"Database error: {e}")
            else:
                st.error(f"Upload Failed: Missing columns: {missing_cols}")

elif menu == "Forecasting":
    render_header("12-Month Advanced Forecasting & 90-Day Roster")
    df = st.session_state.master_data.copy()
    st.metric("Total Rows in PostgreSQL", f"{len(df):,}")
    
    if not df.empty:
        c1, c2 = st.columns(2)
        if role == "Admin":
            if c1.button("🚀 Generate 90-Day Forecast & Overwrite DB"):
                with st.spinner("Analyzing historical patterns and generating 3-month base roster..."):
                    df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
                    df['DoW'] = df['Date'].dt.dayofweek
                    
                    baseline = df.groupby(['Country', 'Channel', 'DoW', 'Time'])[['Volume', 'AHT']].mean().reset_index()
                    
                    start_dt = datetime.now().date() + timedelta(days=1)
                    end_dt = start_dt + timedelta(days=90)
                    future_dates = pd.date_range(start_dt, end_dt)
                    
                    forecast_rows = []
                    schedule_rows = []
                    
                    for d in future_dates:
                        dow = d.dayofweek
                        d_str = d.strftime('%Y-%m-%d')
                        ym_str = d.strftime('%Y-%m')
                        day_base = baseline[baseline['DoW'] == dow]
                        
                        for _, row in day_base.iterrows():
                            # Erlang Math
                            vol = row['Volume'] if not math.isnan(row['Volume']) else 50
                            aht = row['AHT'] if not math.isnan(row['AHT']) else 300
                            
                            req_fte = get_required_fte(vol, aht, 0.80)
                            
                            forecast_rows.append({
                                "Date": d_str, "Time": row['Time'], "Country": row['Country'], 
                                "Channel": row['Channel'], "Forecast_Volume": vol, "Req_FTE": req_fte
                            })
                            
                            # Build base generic agents
                            for i in range(1, req_fte + 1):
                                schedule_rows.append({
                                    "Country": row['Country'], "YearMonth": ym_str, "Date": d_str, "Time": row['Time'],
                                    "Agent": f"Agent_{str(i).zfill(2)}_{row['Country']}", "Base_Activity": "Phone & Cases"
                                })
                    
                    f_df = pd.DataFrame(forecast_rows)
                    s_df = pd.DataFrame(schedule_rows)
                    
                    try:
                        with conn.engine.connect() as c:
                            c.execute(text("DELETE FROM forecast_db"))
                            c.execute(text("DELETE FROM schedule_db"))
                            c.commit()
                        f_df.to_sql('forecast_db', con=conn.engine, if_exists='append', index=False)
                        s_df.to_sql('schedule_db', con=conn.engine, if_exists='append', index=False)
                        
                        st.success(f"Generated {len(f_df)} forecast intervals and {len(s_df)} base schedule rows.")
                        sync_from_cloud()
                    except Exception as e:
                        error_msg = str(e)
                        if "UndefinedColumn" in error_msg:
                            st.error("🚨 **Schema Mismatch Warning:** One of your Supabase tables is missing a column required by the DataFrame.")
                            st.error("Please go to the Supabase Table Editor and ensure both **`forecast_db`** and **`schedule_db`** have a column named **`Time`** (type: text).")
                        else:
                            st.error(f"Database error: {e}")
        
        if not st.session_state.forecast_db.empty:
            f_db = st.session_state.forecast_db
            st.write("### Future Volume Projection")
            if 'Date' in f_db.columns and 'Country' in f_db.columns:
                f_daily = f_db.groupby(['Date', 'Country'])['Forecast_Volume'].sum().reset_index()
                ctry_plot = selected_markets[0] if selected_markets else COUNTRIES[0]
                spain_f = f_daily[f_daily['Country']==ctry_plot]
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=spain_f['Date'], y=spain_f['Forecast_Volume'], name=f"Forecast ({ctry_plot})", line=dict(dash='dot')))
                fig.update_layout(template="plotly_white")
                st.plotly_chart(fig, use_container_width=True)
    else: st.warning("Requires historical data to generate forecast models.")

elif menu == "Scheduling":
    render_header("Master Scheduling & Roster")
    st.write("### Calendar View (Masked)")
    st.markdown("**Layered Roster:** Displays the Base AI Schedule, automatically masked by any Team Leader Approved Exceptions.")
    
    s_db = st.session_state.schedule_db
    e_db = st.session_state.exception_logs
    
    if not s_db.empty and 'Country' in s_db.columns:
        market_db = s_db[s_db['Country'].isin(selected_markets)].copy()
        
        if not market_db.empty and 'Date' in market_db.columns:
            available_dates = sorted(market_db['Date'].unique())
            c1, c2 = st.columns([1, 3])
            selected_date = c1.selectbox("Select Date to View", available_dates)
            
            day_sch = market_db[market_db['Date'] == selected_date].copy()
            
            # --- MASKING LOGIC ENGINE ---
            if not e_db.empty and 'Date' in e_db.columns:
                app_exc = e_db[(e_db['Status'] == 'Approved') & (e_db['Date'] == selected_date)].copy()
                
                # Merge Exception onto Base Schedule
                merged = day_sch.merge(
                    app_exc[['Agent', 'Start Time', 'Type']],
                    left_on=['Agent', 'Time'],
                    right_on=['Agent', 'Start Time'],
                    how='left'
                )
                merged['Live_Status'] = merged['Type'].fillna(merged['Base_Activity'])
                final_df = merged[['Agent', 'Time', 'Live_Status']]
            else:
                final_df = day_sch[['Agent', 'Time', 'Base_Activity']].rename(columns={'Base_Activity': 'Live_Status'})
            
            # Pivot table to make it a calendar
            if 'Time' in final_df.columns:
                pivot_view = final_df.pivot_table(
                    index='Agent',
                    columns='Time',
                    values='Live_Status',
                    aggfunc='first'
                ).fillna("-")
                
                # Sort columns
                sorted_cols = sorted(pivot_view.columns)
                st.dataframe(pivot_view[sorted_cols], use_container_width=True)
            else: st.info("Time column missing in schedule database.")
        else: st.info("No data for selected market.")
    else: st.info("Schedule database is empty.")

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
            t_in = st.selectbox("Reason Code", list(STATUS_DICT.keys()))
            d_in = st.number_input("Duration (Minutes)", value=30, min_value=30, step=30)
            
            if st.form_submit_button("Force Log as Approved"):
                new_e = pd.DataFrame([[ct_in, exc_date.strftime("%Y-%m-%d"), exc_time, agt_in, t_in, d_in, "Manager Override", "Approved"]], columns=["Country", "Date", "Start Time", "Agent", "Type", "Duration (Min)", "Notes", "Status"])
                try: 
                    new_e.to_sql('exception_logs', con=conn.engine, if_exists='append', index=False)
                    st.success("Exception forced as Approved directly to Schedule.")
                    sync_from_cloud()
                except Exception as e:
                    st.error(f"Database error: {e}")

elif menu == "Capacity Planner (Erlang)":
    render_header("Capacity & Headcount Plan Drill-Down")
    f_db = st.session_state.forecast_db
    s_db = st.session_state.schedule_db
    
    if f_db.empty or s_db.empty:
        st.info("Forecast and Schedule databases must be populated.")
    else:
        view_scale = st.radio("Aggregation Level", ["Daily Overview", "Hourly Drill-Down"], horizontal=True)
        
        f_market = f_db[f_db['Country'].isin(selected_markets)]
        s_market = s_db[s_db['Country'].isin(selected_markets)]
        
        if view_scale == "Daily Overview":
            if 'Date' in f_market.columns and 'Req_FTE' in f_market.columns:
                demand = f_market.groupby('Date')['Req_FTE'].max().reset_index()
                supply = s_market.groupby(['Date', 'Agent']).size().reset_index().groupby('Date').size().reset_index(name='Scheduled_FTE')
                gap = demand.merge(supply, on='Date', how='outer').fillna(0)
                gap['Variance'] = gap['Scheduled_FTE'] - gap['Req_FTE']
                
                fig = px.bar(gap, x='Date', y='Variance', color=np.where(gap['Variance'] < 0, 'Understaffed', 'Overstaffed'), color_discrete_map={'Understaffed':'#ef4444', 'Overstaffed':'#10b981'})
                st.plotly_chart(fig, use_container_width=True)
            
        else:
            if 'Date' in f_market.columns:
                dates = sorted(f_market['Date'].unique())
                if dates:
                    sel_date = st.selectbox("Select Date", dates)
                    demand = f_market[f_market['Date'] == sel_date].groupby('Time')['Req_FTE'].sum().reset_index()
                    supply = s_market[s_market['Date'] == sel_date].groupby('Time')['Agent'].count().reset_index(name='Scheduled_FTE')
                    
                    gap = demand.merge(supply, on='Time', how='outer').fillna(0)
                    gap['Variance'] = gap['Scheduled_FTE'] - gap['Req_FTE']
                    gap = gap.sort_values(by='Time')
                    
                    fig = go.Figure(go.Bar(x=gap['Time'], y=gap['Variance'], marker_color=np.where(gap['Variance'] < 0, '#ef4444', '#10b981')))
                    fig.update_layout(template="plotly_white", title="FTE Variance by 30-Min Interval")
                    st.plotly_chart(fig, use_container_width=True)

elif menu == "Real-Time Ops":
    render_header("Live Command Center")
    st.warning("⚠️ INTEGRATION STATUS: Placeholder mode. Awaiting API Webhooks for Salesforce and Talkdesk.")
    
    c1, c2 = st.columns(2)
    with c1:
        st.write("### Talkdesk: Calls Waiting in Queue")
        st.bar_chart(np.random.randint(0, 10, size=12), color=DP_NAVY)
    with c2:
        st.write("### Salesforce: Average Backlog Age")
        st.line_chart(np.random.randint(20, 120, size=12), color=DP_TEAL)

elif menu == "Admin Panel":
    render_header("Access Management & Documentation")
    
    t1, t2 = st.tabs(["⚙️ Access Control", "📘 Operations Manual"])
    with t1:
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
        
    with t2:
        st.markdown("""
        ### 📖 Docplanner WFM Master Guide
        
        #### 1. Data Ingestion
        To process raw interaction data, go to the **Import Data** tab. Upload the `telmo_forecast_v1` CSV. The system natively translates the `date_timestamp` into strict 30-minute intervals and converts `aht_minutes` into usable seconds.
        
        #### 2. The Layered Database (Masking)
        To ensure we can report on **Adherence** (Planned vs Reality), this tool never deletes shifts. 
        * **Base Schedule:** AI generates the baseline shift (e.g., 'Phone & Cases').
        * **Exceptions:** If a TL approves an exception (e.g., '1:1'), the system layers it over the Base Schedule in the Master Roster UI.
        
        #### 3. 90-Day Rolling Roster
        Admins must run the **Forecasting** tool to generate future data. It uses the Master Database to build day-of-week averages, pushes them through the Erlang-C engine, and constructs exactly 90 days of interval-level schedule blocks.
        
        #### 4. Status Dictionary
        """)
        manual_df = pd.DataFrame(list(STATUS_DICT.items()), columns=['Status', 'Usage Guidelines'])
        st.dataframe(manual_df, use_container_width=True, hide_index=True)

elif menu == "Agent Portal":
    render_header("My Agent Portal")
    s_db = st.session_state.schedule_db
    e_db = st.session_state.exception_logs
    
    st.write("### 🗓️ My Published Shifts (Masked)")
    if not s_db.empty and 'Agent' in s_db.columns:
        my_sch = s_db[s_db['Agent'].str.lower() == st.session_state.current_email.lower()].copy()
        if not my_sch.empty:
            if not e_db.empty and 'Agent' in e_db.columns:
                my_exc = e_db[(e_db['Agent'].str.lower() == st.session_state.current_email.lower()) & (e_db['Status'] == 'Approved')]
                merged = my_sch.merge(my_exc[['Date', 'Start Time', 'Type']], left_on=['Date', 'Time'], right_on=['Date', 'Start Time'], how='left')
                merged['Live_Status'] = merged['Type'].fillna(merged['Base_Activity'])
                view_df = merged[['Date', 'Time', 'Live_Status']]
            else:
                view_df = my_sch[['Date', 'Time', 'Base_Activity']].rename(columns={'Base_Activity': 'Live_Status'})
                
            pivot = view_df.pivot_table(index='Date', columns='Time', values='Live_Status', aggfunc='first').fillna("-")
            sorted_cols = sorted(pivot.columns)
            st.dataframe(pivot[sorted_cols], use_container_width=True)
        else: st.warning("No schedule records found for your Docplanner email.")
    else: st.info("Schedule database is empty.")

    st.divider()
    st.write("### ⚠️ Submit Exception Request (To Manager)")
    with st.form("agent_exc_request", clear_on_submit=True):
        c1, c2 = st.columns(2)
        exc_date = c1.date_input("Date of Exception")
        exc_time = c2.selectbox("Start Time", generate_time_slots())
        t_in = st.selectbox("Reason Category", list(STATUS_DICT.keys()))
        d_in = st.number_input("Duration Missing (Minutes)", value=30, min_value=30, step=30)
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

elif menu == "Reporting Center":
    render_header("Data Exports")
    if not st.session_state.master_data.empty and 'Country' in st.session_state.master_data.columns:
        csv = st.session_state.master_data.to_csv(index=False).encode('utf-8')
        st.download_button("Export Global Master Data (CSV)", data=csv, file_name="WFM_Global_Export.csv", mime="text/csv")
    else: st.warning("No data available to export.")

elif menu == "System Status":
    render_header("Infrastructure Health")
    c1, c2, c3 = st.columns(3)
    c1.metric("Database Platform", "Supabase (PostgreSQL)")
    c2.metric("Master Data Rows", len(st.session_state.master_data))
    c3.metric("Service Latency", "< 5ms")
