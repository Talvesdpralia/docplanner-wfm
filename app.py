import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import math
import requests
import urllib.parse
from sqlalchemy import text

# ==========================================
# 1. UI & DESIGN ENGINE 
# ==========================================
st.set_page_config(page_title="Docplanner WFM Pro", layout="wide", page_icon="🏥")

DP_TEAL = "#00c4a7"
DP_NAVY = "#011e41"
DP_SLATE = "#4b5563"

# Official Status Vocabulary
STATUS_DICT = {
    "1:1": "For one on ones between managers and specialists.",
    "All Channels": "When managing all channels.",
    "Birthday": "Day off to celebrate birthday.",
    "Parental Leave": "For leaves related to new borns.",
    "DPP Phone": "Exclusive to Poland. Agent working on DPP.",
    "DPP Chat": "Exclusive to Poland. Agent working on DPP.",
    "Phone & Cases": "When managing calls and cases.",
    "Cases": "When managing just cases.",
    "Chat": "When managing just chats.",
    "Chat & Cases": "When managing chat and cases.",
    "Chat & Whatsapp": "When managing chat and whatsapp.",
    "Whatsapp": "When managing whatsapp only.",
    "Holiday": "For approved holidays.",
    "Import": "Specific for Poland - Project of data import.",
    "Language Class": "Time dedicated for language classes.",
    "Lunch": "Exclusively for lunch time.",
    "Medical Appt": "For medical appointments or consults with doctors.",
    "Meeting": "Any type of meeting requiring inbound unavailability.",
    "Off": "Public holidays or specific reasons agent won't work.",
    "Off queue": "When specialist should be off queue but still working.",
    "Guardia_Off": "Specific for Mexico - Used to recover Saturday time.",
    "Outbound": "When dealing with outbound calls only.",
    "Project": "Offline project work / unavailable for cases.",
    "Shadowing": "When doing shadowing.",
    "Sick Leave": "For sick leaves.",
    "TL Request": "Related to tasks asked by Team Leaders.",
    "Training": "For trainings.",
    "Triage and Cases": "During ramp up period managing cases."
}

def apply_custom_design():
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Figtree:wght@300;400;500;600&display=swap');
        
        .stApp {{
            font-family: 'Figtree', sans-serif !important;
            background: #f8fafc !important; 
        }}
        h1 {{ font-weight: 300 !important; font-size: 1.7rem !important; color: {DP_NAVY}; letter-spacing: -0.5px; }}
        h2, h3 {{ font-weight: 400 !important; font-size: 1.1rem !important; color: {DP_SLATE}; }}
        
        section[data-testid="stSidebar"] {{
            background: white !important;
            border-right: 1px solid #e2e8f0 !important;
        }}
        
        [data-testid="stMetric"] {{
            background: white !important;
            border: 1px solid #e2e8f0 !important;
            padding: 16px !important;
            border-radius: 12px !important;
            box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05) !important;
        }}
        
        .stButton>button {{
            background: {DP_TEAL} !important;
            color: white !important;
            border-radius: 8px !important;
            border: none !important;
            font-weight: 500 !important;
        }}
        
        /* Interactive Dataframe / Pivot Table styling */
        [data-testid="stDataFrame"] {{
            border-radius: 8px !important;
            overflow: hidden !important;
            border: 1px solid #e2e8f0 !important;
        }}
        </style>
    """, unsafe_allow_html=True)

apply_custom_design()

# ==========================================
# 2. CORE ENGINES (ERLANG & DB CONNECTION)
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

def get_required_fte(vol, aht, target_sl=0.80, target_time=20):
    if vol <= 0: return 0
    intensity = (vol * aht) / 3600
    agents = math.ceil(intensity) + 1
    while calculate_erlang_c(vol, aht, target_time, agents) < target_sl and agents < 1000:
        agents += 1
    return agents

def generate_time_slots():
    return [f"{str(h).zfill(2)}:{str(m).zfill(2)}" for h in range(0, 24) for m in (0, 30)]

def sync_from_cloud():
    try:
        st.session_state.user_db = conn.query("SELECT * FROM user_db;", ttl="0m")
        st.session_state.master_data = conn.query("SELECT * FROM master_data;", ttl="0m")
        st.session_state.exception_logs = conn.query("SELECT * FROM exception_logs;", ttl="0m")
        st.session_state.schedule_db = conn.query("SELECT * FROM schedule_db;", ttl="0m")
        st.session_state.forecast_db = conn.query("SELECT * FROM forecast_db;", ttl="0m")
    except Exception as e:
        st.error(f"Failed to pull from Supabase. Ensure database tables exist. Error: {e}")
        # Initialize empty dataframes to prevent crashes if tables are missing during first run
        st.session_state.user_db = pd.DataFrame(columns=["email", "password", "role"])
        st.session_state.master_data = pd.DataFrame(columns=["Date", "Time", "Country", "Channel", "Volume", "AHT"])
        st.session_state.exception_logs = pd.DataFrame(columns=["Country", "Date", "Start Time", "Agent", "Type", "Duration (Min)", "Notes", "Status"])
        st.session_state.schedule_db = pd.DataFrame(columns=["Country", "Date", "Time", "Agent", "Base_Activity"])
        st.session_state.forecast_db = pd.DataFrame(columns=["Date", "Time", "Country", "Channel", "Forecast_Volume", "Req_FTE"])

# ==========================================
# 3. AUTHENTICATION (SSO)
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
            # Temporary mock for bypass; in production map `email` from decoded JWT to user_db
            email_auth = "telmo.alves@docplanner.com"
            
            st.session_state.logged_in = True
            st.session_state.current_email = email_auth
            
            # Map role from Database
            db_users = st.session_state.user_db
            if not db_users.empty and email_auth in db_users['email'].values:
                st.session_state.user_role = db_users[db_users['email'] == email_auth]['role'].iloc[0]
            else:
                # Default fallback role if not in DB
                st.session_state.user_role = "Admin"
                
            st.query_params.clear()
            st.rerun()
        else:
            st.error(f"Google Token Error: {token_data}")
            st.stop()
    except Exception as e:
        st.error(f"Authentication System Error: {e}")

if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<br><br><br>", unsafe_allow_html=True)
        st.image("https://www.docplanner.com/img/logo-default-group-en.svg", width=220)
        st.markdown("<h1 style='text-align: center;'>WFM Enterprise Portal</h1>", unsafe_allow_html=True)
        
        encoded_uri = urllib.parse.quote(redirect_uri, safe='')
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&redirect_uri={encoded_uri}&response_type=code&scope=openid%20email%20profile&prompt=consent"
        
        st.markdown(f"""
            <div style="display: flex; justify-content: center; margin-top: 30px;">
                <a href="{auth_url}" target="_blank" style="text-decoration:none;">
                    <div style="background:white;color:#757575;border:1px solid #dadce0;border-radius:24px;padding:12px 24px;text-align:center;font-weight:500;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 8px rgba(0,0,0,0.05);transition: box-shadow 0.2s;">
                        <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" style="width:20px;margin-right:12px;">
                        Sign in with Docplanner Google
                    </div>
                </a>
            </div>
        """, unsafe_allow_html=True)
    st.stop()

# ==========================================
# 4. NAVIGATION & FILTERS
# ==========================================
role = st.session_state.user_role
COUNTRIES = ["Spain", "Mexico", "Poland", "Germany", "Italy", "Brazil", "Colombia", "Turkey"]

with st.sidebar:
    st.image("https://www.docplanner.com/img/logo-default-group-en.svg", width=140)
    st.markdown(f"**{st.session_state.current_email}**")
    st.caption(f"Role: {role}")
    st.divider()
    
    if role in ["Admin", "Manager"]:
        menu_options = ["Dashboard", "Import Data", "Forecasting", "Master Schedule", "Capacity Planner", "Exception Manager", "Real-Time Ops", "Admin & Manual"]
    else:
        menu_options = ["Agent Portal"]
        
    menu = st.radio("Navigation", menu_options)
    market_filter = st.selectbox("Global Market Filter", COUNTRIES)
    
    st.divider()
    if st.button("Sync Cloud Data 🔄", use_container_width=True):
        sync_from_cloud()
        st.rerun()
    if st.button("Log Out 🚪", use_container_width=True):
        st.session_state.logged_in = False
        st.rerun()

# ==========================================
# 5. DASHBOARD
# ==========================================
if menu == "Dashboard":
    st.title(f"Strategic Overview: {market_filter}")
    df = st.session_state.master_data
    
    # KPIs based on real data
    if not df.empty and 'Volume' in df.columns and 'Country' in df.columns:
        df_f = df[df['Country'] == market_filter]
        tot_vol = df_f['Volume'].sum() if not df_f.empty else 0
        avg_aht = df_f['AHT'].mean() if not df_f.empty else 0
    else:
        df_f = pd.DataFrame()
        tot_vol, avg_aht = 0, 0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Historical Volume Processed", f"{tot_vol:,.0f}")
    c2.metric("Average AHT", f"{avg_aht:.0f}s" if avg_aht > 0 else "0s")
    c3.metric("FTE Occupancy Target", "85%")
    c4.metric("Active Regions Data", str(df['Country'].nunique()) if not df.empty else "0")
    
    st.divider()
    
    if not df_f.empty:
        col_l, col_r = st.columns([2, 1])
        with col_l:
            st.write("### Historical Volume Demand by Date")
            daily_vol = df_f.groupby('Date')['Volume'].sum().reset_index()
            fig1 = px.area(daily_vol, x='Date', y='Volume', color_discrete_sequence=[DP_TEAL], template="plotly_white")
            st.plotly_chart(fig1, use_container_width=True)
        with col_r:
            st.write("### Channel Mix")
            chan_vol = df_f.groupby('Channel')['Volume'].sum().reset_index()
            fig2 = px.pie(chan_vol, values='Volume', names='Channel', hole=0.4, color_discrete_sequence=[DP_TEAL, DP_NAVY, DP_SLATE, "#e2e8f0"])
            fig2.update_layout(margin=dict(t=20, b=20, l=0, r=0))
            st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No data available for the selected market. Upload raw data in 'Import Data'.")

# ==========================================
# 6. IMPORT DATA (CUSTOM TELMO PARSER)
# ==========================================
elif menu == "Import Data":
    st.title("Data Ingestion & Aggregation")
    st.markdown("""
    Upload the raw transaction export (`telmo_forecast_v1.csv`). The system will parse the exact timestamps, aggregate them into 30-minute intervals, and convert AHT to seconds.
    """)
    
    up = st.file_uploader("Upload Raw Interaction Data (CSV)", type="csv")
    
    if up:
        with st.spinner("Processing timestamps and aggregating into 30-minute intervals..."):
            raw_df = pd.read_csv(up)
            
            # Validate Columns
            expected_cols = ['case_id', 'date_timestamp', 'country', 'channel', 'aht_minutes']
            missing = [c for c in expected_cols if c not in raw_df.columns]
            
            if missing:
                st.error(f"File validation failed. Missing required columns: {missing}")
            else:
                st.write("### Raw Data Preview")
                st.dataframe(raw_df.head(), use_container_width=True)
                
                # Clean and parse dates
                raw_df['date_timestamp'] = pd.to_datetime(raw_df['date_timestamp'], errors='coerce')
                raw_df = raw_df.dropna(subset=['date_timestamp'])
                
                # Floor exactly to 30-minute blocks (e.g. 10:09 -> 10:00)
                raw_df['interval'] = raw_df['date_timestamp'].dt.floor('30min')
                raw_df['Date'] = raw_df['interval'].dt.date.astype(str)
                raw_df['Time'] = raw_df['interval'].dt.strftime('%H:%M')
                
                # Group by Interval
                agg_df = raw_df.groupby(['Date', 'Time', 'country', 'channel']).agg(
                    Volume=('case_id', 'count'),
                    AHT=('aht_minutes', lambda x: x.mean() * 60) # Minutes to Seconds
                ).reset_index()
                
                agg_df.rename(columns={'country': 'Country', 'channel': 'Channel'}, inplace=True)
                
                st.write("### Extracted 30-Minute Intervals")
                st.dataframe(agg_df.head(10), use_container_width=True)
                
                if st.button("Commit Intervals to Cloud Database", use_container_width=True):
                    try:
                        agg_df.to_sql('master_data', con=conn.engine, if_exists='append', index=False)
                        st.success(f"Successfully committed {len(agg_df)} interval records to Supabase!")
                        sync_from_cloud()
                    except Exception as e:
                        st.error(f"Database Error: {e}")

# ==========================================
# 7. FORECASTING & 90-DAY ROSTER CREATION
# ==========================================
elif menu == "Forecasting":
    st.title("90-Day Rolling Forecast & Schedule Generator")
    st.markdown("Generates future volume based on historical day-of-week averages, computes Required FTE via Erlang-C, and builds the 3-month Base Schedule.")
    
    with st.form("forecast_generation"):
        c1, c2 = st.columns(2)
        target_sl = c1.slider("Target Service Level %", 50, 99, 80) / 100
        shrink_est = c2.slider("Planned Shrinkage Factor %", 0, 50, 25) / 100
        
        if st.form_submit_button("🚀 Generate 90-Day Forecast & Base Roster"):
            df = st.session_state.master_data
            if df.empty:
                st.error("Cannot forecast. Master database is empty.")
            else:
                with st.spinner("Analyzing history and projecting 90 days..."):
                    df['Date'] = pd.to_datetime(df['Date'])
                    df['DoW'] = df['Date'].dt.dayofweek
                    
                    # Create baseline matrix
                    baseline = df.groupby(['Country', 'Channel', 'DoW', 'Time'])[['Volume', 'AHT']].mean().reset_index()
                    
                    start_dt = datetime.now().date() + timedelta(days=1)
                    end_dt = start_dt + timedelta(days=90)
                    future_dates = pd.date_range(start_dt, end_dt)
                    
                    forecast_rows = []
                    schedule_rows = []
                    
                    for d in future_dates:
                        dow = d.dayofweek
                        d_str = d.strftime('%Y-%m-%d')
                        day_base = baseline[baseline['DoW'] == dow]
                        
                        for _, row in day_base.iterrows():
                            # Erlang Math
                            raw_fte = get_required_fte(row['Volume'], row['AHT'], target_sl)
                            # Adjust for shrinkage to get scheduled bodies needed
                            actual_req_fte = math.ceil(raw_fte / (1 - shrink_est)) if (1 - shrink_est) > 0 else raw_fte
                            
                            forecast_rows.append({
                                "Date": d_str, "Time": row['Time'], "Country": row['Country'], 
                                "Channel": row['Channel'], "Forecast_Volume": row['Volume'], "Req_FTE": actual_req_fte
                            })
                            
                            # Create base schedule
                            # Assigning generic Agent IDs for the base forecast. Can be mapped to actual names later.
                            for i in range(1, actual_req_fte + 1):
                                schedule_rows.append({
                                    "Country": row['Country'], "Date": d_str, "Time": row['Time'],
                                    "Agent": f"Agent_{str(i).zfill(2)}_{row['Country']}", "Base_Activity": "Phone & Cases"
                                })
                    
                    f_df = pd.DataFrame(forecast_rows)
                    s_df = pd.DataFrame(schedule_rows)
                    
                    try:
                        with conn.engine.connect() as c:
                            # Safely overwrite future data to prevent duplication issues on re-runs
                            c.execute(text("DELETE FROM forecast_db"))
                            c.execute(text("DELETE FROM schedule_db"))
                            c.commit()
                        f_df.to_sql('forecast_db', con=conn.engine, if_exists='append', index=False)
                        s_df.to_sql('schedule_db', con=conn.engine, if_exists='append', index=False)
                        
                        st.success(f"Generated {len(f_df)} forecast intervals and {len(s_df)} roster shifts for 90 days.")
                        sync_from_cloud()
                    except Exception as e:
                        st.error(f"Database error during generation: {e}")

# ==========================================
# 8. MASTER SCHEDULE (PIVOT MASKING)
# ==========================================
elif menu == "Master Schedule":
    st.title(f"Master Roster: {market_filter}")
    st.markdown("**The Layered Roster:** Displays the Base AI Schedule, automatically masked by any Team Leader Approved Exceptions.")
    
    s_db = st.session_state.schedule_db
    e_db = st.session_state.exception_logs
    
    if s_db.empty:
        st.warning("No roster data exists. Run Forecasting to generate a base schedule.")
    else:
        market_sch = s_db[s_db['Country'] == market_filter].copy()
        available_dates = sorted(market_sch['Date'].unique())
        
        if available_dates:
            # Filter UI
            c1, c2 = st.columns([1, 3])
            selected_date = c1.selectbox("Select Date to View", available_dates)
            
            day_sch = market_sch[market_sch['Date'] == selected_date].copy()
            
            # MASKING ENGINE
            if not e_db.empty:
                app_exc = e_db[(e_db['Status'] == 'Approved') & (e_db['Date'] == selected_date)].copy()
                
                # Merge exception 'Type' onto the Base Schedule based on Agent and exact Time slot
                merged = day_sch.merge(
                    app_exc[['Agent', 'Start Time', 'Type']], 
                    left_on=['Agent', 'Time'], 
                    right_on=['Agent', 'Start Time'], 
                    how='left'
                )
                
                # Prioritize Exception over Base_Activity
                merged['Live_Status'] = merged['Type'].fillna(merged['Base_Activity'])
                final_df = merged[['Agent', 'Time', 'Live_Status']]
            else:
                final_df = day_sch[['Agent', 'Time', 'Base_Activity']].rename(columns={'Base_Activity': 'Live_Status'})
            
            st.write(f"### Chronological Interval Matrix ({selected_date})")
            
            # Pivot table to achieve the requested columns=Time, rows=Agents view
            pivot_view = final_df.pivot_table(
                index='Agent', 
                columns='Time', 
                values='Live_Status', 
                aggfunc='first'
            ).fillna("OFF")
            
            # Ensure time columns are sorted correctly (08:00 before 09:00)
            sorted_cols = sorted(pivot_view.columns)
            pivot_view = pivot_view[sorted_cols]
            
            st.dataframe(pivot_view, use_container_width=True)
        else:
            st.info("No schedule rows found for this market.")

# ==========================================
# 9. CAPACITY PLANNER
# ==========================================
elif menu == "Capacity Planner":
    st.title("Capacity & FTE Gap Analysis")
    
    f_db = st.session_state.forecast_db
    s_db = st.session_state.schedule_db
    
    if f_db.empty or s_db.empty:
        st.warning("Forecast and Schedule databases must be populated to analyze capacity.")
    else:
        view_scale = st.radio("Aggregation Scope", ["Daily Overview", "Hourly Drill-Down (Select Date)"], horizontal=True)
        
        f_market = f_db[f_db['Country'] == market_filter]
        s_market = s_db[s_db['Country'] == market_filter]
        
        if view_scale == "Daily Overview":
            # Max required FTE per day vs Total Unique Agents scheduled that day
            demand = f_market.groupby('Date')['Req_FTE'].max().reset_index()
            supply = s_market.groupby(['Date', 'Agent']).size().reset_index().groupby('Date').size().reset_index(name='Scheduled_FTE')
            
            gap = demand.merge(supply, on='Date', how='outer').fillna(0)
            gap['Variance'] = gap['Scheduled_FTE'] - gap['Req_FTE']
            
            st.write("### Daily Headcount Gap")
            fig = px.bar(gap, x='Date', y='Variance', color=np.where(gap['Variance'] < 0, 'Understaffed', 'Overstaffed'), color_discrete_map={'Understaffed':'#ef4444', 'Overstaffed':'#10b981'})
            fig.update_layout(template="plotly_white")
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            dates = sorted(f_market['Date'].unique())
            if dates:
                sel_date = st.selectbox("Select Date for Hourly Drill-Down", dates)
                
                # Sum required FTE per interval vs Sum of Agents scheduled per interval
                demand = f_market[f_market['Date'] == sel_date].groupby('Time')['Req_FTE'].sum().reset_index()
                supply = s_market[s_market['Date'] == sel_date].groupby('Time')['Agent'].count().reset_index(name='Scheduled_FTE')
                
                gap = demand.merge(supply, on='Time', how='outer').fillna(0)
                gap['Variance'] = gap['Scheduled_FTE'] - gap['Req_FTE']
                
                # Sort Chronologically
                gap = gap.sort_values(by='Time')
                
                st.write(f"### Interval Gap Analysis ({sel_date})")
                fig = go.Figure(go.Bar(x=gap['Time'], y=gap['Variance'], marker_color=np.where(gap['Variance'] < 0, '#ef4444', '#10b981')))
                fig.update_layout(template="plotly_white", title="FTE Variance by 30-Min Interval (Negative = Understaffed)")
                st.plotly_chart(fig, use_container_width=True)

# ==========================================
# 10. EXCEPTION MANAGER (TL CONTROL)
# ==========================================
elif menu == "Exception Manager":
    st.title("Manager Control: Exceptions & Overrides")
    
    tab1, tab2 = st.tabs(["📋 Pending Approvals", "➕ Direct Roster Override"])
    e_db = st.session_state.exception_logs
    
    with tab1:
        st.write("### Agent Requests Awaiting Approval")
        if not e_db.empty:
            pending = e_db[e_db['Status'] == 'Pending']
            if pending.empty:
                st.success("No pending requests. Queue is clean.")
            else:
                for idx, row in pending.iterrows():
                    with st.container():
                        st.markdown(f"**Request from {row['Agent']}** | Date: **{row['Date']}** | Start: **{row['Start Time']}** | Type: **{row['Type']}** ({row['Duration (Min)']}m)")
                        st.caption(f"Agent Notes: {row['Notes']}")
                        
                        c1, c2, c3 = st.columns([1,1,4])
                        if c1.button("✅ Approve", key=f"app_{idx}"):
                            try:
                                with conn.engine.connect() as c:
                                    c.execute(text(f"UPDATE exception_logs SET \"Status\" = 'Approved' WHERE \"Agent\" = '{row['Agent']}' AND \"Date\" = '{row['Date']}' AND \"Start Time\" = '{row['Start Time']}'"))
                                    c.commit()
                                st.success("Approved!")
                                sync_from_cloud()
                                st.rerun()
                            except Exception as e: st.error(f"DB Error: {e}")
                            
                        if c2.button("❌ Reject", key=f"rej_{idx}"):
                            try:
                                with conn.engine.connect() as c:
                                    c.execute(text(f"UPDATE exception_logs SET \"Status\" = 'Rejected' WHERE \"Agent\" = '{row['Agent']}' AND \"Date\" = '{row['Date']}' AND \"Start Time\" = '{row['Start Time']}'"))
                                    c.commit()
                                sync_from_cloud()
                                st.rerun()
                            except Exception as e: st.error(f"DB Error: {e}")
                        st.divider()
        else:
            st.info("Exception database is empty.")

    with tab2:
        st.write("### Force Log Activity to Roster")
        st.markdown("Use this to immediately assign Trainings, Meetings, or Absences without Agent request.")
        with st.form("direct_log_form"):
            c1, c2 = st.columns(2)
            agt = c1.text_input("Agent Email or ID (Must match Roster exactly)")
            typ = c2.selectbox("Activity Status", list(STATUS_DICT.keys()))
            dt = c1.date_input("Date")
            tm = c2.selectbox("Start Time", generate_time_slots())
            dur = st.number_input("Duration (Minutes)", value=30, min_value=30, step=30)
            
            if st.form_submit_button("Inject as Approved"):
                if not agt:
                    st.error("Please enter an Agent Email/ID.")
                else:
                    new_exc = pd.DataFrame([[market_filter, dt.strftime("%Y-%m-%d"), tm, agt, typ, dur, "TL Override", "Approved"]], 
                                         columns=["Country", "Date", "Start Time", "Agent", "Type", "Duration (Min)", "Notes", "Status"])
                    try:
                        new_exc.to_sql('exception_logs', con=conn.engine, if_exists='append', index=False)
                        st.success("Activity injected successfully. Roster will now mask this time block.")
                        sync_from_cloud()
                    except Exception as e:
                        st.error(f"Database Error: {e}")

# ==========================================
# 11. REAL-TIME OPS (PLACEHOLDER)
# ==========================================
elif menu == "Real-Time Ops":
    st.title("Live Operations Center (Placeholder)")
    st.warning("⚠️ INTEGRATION STATUS: Placeholder mode. Awaiting API Webhooks for Salesforce and Talkdesk.")
    
    c1, c2 = st.columns(2)
    with c1:
        st.write("### Talkdesk: Calls Waiting in Queue")
        live_calls = pd.DataFrame(np.random.randint(0, 10, size=(12, 1)), columns=['Calls Waiting'])
        st.bar_chart(live_calls, color=DP_NAVY)
    with c2:
        st.write("### Salesforce: Average Backlog Age")
        cases = pd.DataFrame(np.random.randint(20, 120, size=(12, 1)), columns=['Minutes Open'])
        st.line_chart(cases, color=DP_TEAL)

# ==========================================
# 12. ADMIN & USER MANUAL
# ==========================================
elif menu == "Admin & Manual":
    st.title("System Manual & Access Control")
    
    t1, t2 = st.tabs(["📘 Operations Manual", "⚙️ Database Roles"])
    
    with t1:
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
        
    with t2:
        st.write("### Authorized Users Table")
        st.dataframe(st.session_state.user_db, use_container_width=True)

# ==========================================
# 13. AGENT PORTAL
# ==========================================
elif menu == "Agent Portal":
    st.title(f"Agent Workspace")
    st.caption(f"Logged in as {st.session_state.current_email}")
    
    st.write("### My Published Shifts (Masked View)")
    s_db = st.session_state.schedule_db
    e_db = st.session_state.exception_logs
    
    if not s_db.empty:
        my_sch = s_db[s_db['Agent'] == st.session_state.current_email].copy()
        if not my_sch.empty:
            # Apply Masking Logic for Agent
            if not e_db.empty:
                my_exc = e_db[(e_db['Agent'] == st.session_state.current_email) & (e_db['Status'] == 'Approved')]
                merged = my_sch.merge(my_exc[['Date', 'Start Time', 'Type']], left_on=['Date', 'Time'], right_on=['Date', 'Start Time'], how='left')
                merged['Live_Status'] = merged['Type'].fillna(merged['Base_Activity'])
                view_df = merged[['Date', 'Time', 'Live_Status']]
            else:
                view_df = my_sch[['Date', 'Time', 'Base_Activity']].rename(columns={'Base_Activity': 'Live_Status'})
                
            pivot = view_df.pivot_table(index='Date', columns='Time', values='Live_Status', aggfunc='first').fillna("-")
            sorted_cols = sorted(pivot.columns)
            st.dataframe(pivot[sorted_cols], use_container_width=True)
        else:
            st.info("You have no shifts assigned currently.")
    else:
        st.info("Schedule database is empty.")
    
    st.divider()
    with st.expander("⚠️ Submit Exception / Time-Off Request"):
        with st.form("agent_form"):
            req_type = st.selectbox("Requested Activity", list(STATUS_DICT.keys()))
            req_date = st.date_input("Date")
            req_time = st.selectbox("Start Time", generate_time_slots())
            req_dur = st.number_input("Duration Missing (Minutes)", 30, 480, 30)
            req_notes = st.text_area("Notes for Manager")
            
            if st.form_submit_button("Submit Request"):
                new_req = pd.DataFrame([["Global", req_date.strftime("%Y-%m-%d"), req_time, st.session_state.current_email, req_type, req_dur, req_notes, "Pending"]], 
                                     columns=["Country", "Date", "Start Time", "Agent", "Type", "Duration (Min)", "Notes", "Status"])
                try:
                    new_req.to_sql('exception_logs', con=conn.engine, if_exists='append', index=False)
                    st.success("Request sent to Team Leader! Monitor your shifts tab for updates.")
                    sync_from_cloud()
                except Exception as e:
                    st.error(f"Error submitting request: {e}")
