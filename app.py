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

# Google Auth Imports
from google.oauth2 import id_token
import google.auth.transport.requests

# ==========================================
# 1. UI & DESIGN ENGINE - PREMIUM GLASS
# ==========================================
st.set_page_config(page_title="Docplanner WFM Pro", layout="wide", page_icon="🏥")

DP_TEAL, DP_NAVY, DP_SLATE = "#00c4a7", "#011e41", "#4b5563"

STATUS_DICT = {
    "1:1": "For one on ones between managers and specialists.", "All Channels": "When managing all channels.",
    "Birthday": "Day off to celebrate birthday", "Parental Leave": "For leaves related to new borns.",
    "DPP Phone": "Exclusive to Poland. Agent working on DPP", "DPP Chat": "Exclusive to Poland. Agent working on DPP",
    "Phone & Cases": "When managing calls and cases.", "Cases": "When managing just cases.",
    "Chat": "When managing just chats.", "Chat & Cases": "When managing chat and cases.",
    "Chat & Whatsapp": "When managing chat and whatsapp.", "Whatsapp": "When managing whatsapp only.",
    "Holiday": "For approved holidays.", "Import": "Specific for Poland - Project of data import",
    "Language Class": "Time dedicated for language classes", "Lunch": "Exclusively for lunch time.",
    "Medical Appt": "For medical appointments or consults with doctors.", "Meeting": "For any type of meeting.",
    "Off": "For public holidays or specific reasons where the agent won´t work", "Off queue": "Off queue but working.",
    "Guardia_Off": "Specific for Mexico - Recover time", "Outbound": "When dealing with outbound calls only",
    "Project": "Working on a project.", "Shadowing": "When doing shadowing.",
    "Sick Leave": "For sick leaves.", "TL Request": "Related to tasks asked by Team Leaders",
    "Training": "For trainings.", "Triage and Cases": "During ramp up period but already managing cases."
}

def apply_custom_design():
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Figtree:wght@300;400;500;600&display=swap');
        .stApp {{ font-family: 'Figtree', sans-serif !important; background: radial-gradient(circle at 10% 40%, rgba(0, 196, 167, 0.05), transparent 40%), radial-gradient(circle at 90% 10%, rgba(1, 30, 65, 0.04), transparent 40%), #f8fafc !important; }}
        h1 {{ font-weight: 300 !important; font-size: 1.7rem !important; color: {DP_NAVY}; letter-spacing: -0.5px; }}
        h2, h3 {{ font-weight: 400 !important; font-size: 1.1rem !important; color: {DP_SLATE}; }}
        p, span, label, div[data-baseweb="select"] {{ font-size: 13.5px !important; }}
        section[data-testid="stSidebar"] {{ background: rgba(255, 255, 255, 0.1) !important; backdrop-filter: blur(40px) saturate(200%) !important; border-right: 1px solid rgba(255, 255, 255, 0.4) !important; box-shadow: 4px 0 24px rgba(0,0,0,0.02) !important; }}
        [data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child {{ display: none !important; }}
        [data-testid="stSidebar"] div[role="radiogroup"] label {{ background: transparent !important; padding: 6px 12px !important; margin-bottom: 2px !important; border-radius: 8px !important; transition: all 0.2s ease !important; color: {DP_NAVY} !important; font-weight: 400 !important; border-left: 3px solid transparent !important; }}
        [data-testid="stSidebar"] div[role="radiogroup"] label:hover {{ background: rgba(0, 196, 167, 0.04) !important; }}
        [data-testid="stSidebar"] div[role="radiogroup"] label[aria-checked="true"], [data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] {{ background: rgba(0, 196, 167, 0.06) !important; border-left: 3px solid {DP_TEAL} !important; color: {DP_TEAL} !important; font-weight: 600 !important; }}
        div[role="radiogroup"] div[data-testid="stMarkdownContainer"] ~ div[aria-checked="true"] div:first-child, div[role="radiogroup"] div[data-testid="stMarkdownContainer"] ~ div[data-checked="true"] div:first-child {{ background-color: {DP_TEAL} !important; border-color: {DP_TEAL} !important; }}
        input[type="radio"] {{ accent-color: {DP_TEAL} !important; }}
        div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="select"] > div {{ background-color: rgba(255, 255, 255, 0.9) !important; border: 1px solid rgba(0,0,0,0.03) !important; border-radius: 20px !important; box-shadow: 0 2px 8px rgba(0,0,0,0.02), 0 1px 2px rgba(0,0,0,0.02) !important; padding: 2px 8px !important; transition: box-shadow 0.2s ease !important; }}
        div[data-baseweb="input"]:focus-within, div[data-baseweb="select"] > div:focus-within {{ box-shadow: 0 8px 20px rgba(0, 196, 167, 0.1) !important; border: 1px solid rgba(0, 196, 167, 0.4) !important; }}
        .stTextInput input, .stNumberInput input {{ background-color: transparent !important; border: none !important; box-shadow: none !important; padding: 8px !important; }}
        [data-testid="stMetric"] {{ background: rgba(255, 255, 255, 0.6) !important; backdrop-filter: blur(15px); border: 1px solid rgba(255, 255, 255, 0.8) !important; padding: 16px !important; border-radius: 16px !important; box-shadow: 0 4px 15px rgba(0,0,0,0.02) !important; }}
        .stButton>button {{ background: {DP_TEAL} !important; color: white !important; border-radius: 20px !important; border: none !important; padding: 8px 24px !important; font-weight: 500 !important; box-shadow: 0 4px 12px rgba(0, 196, 167, 0.2) !important; }}
        </style>
    """, unsafe_allow_html=True)

def ui_divider(margin="10px"):
    st.markdown(f"<hr style='margin: {margin} 0; border-color: rgba(0,0,0,0.05);'>", unsafe_allow_html=True)

apply_custom_design()

# ==========================================
# 2. CORE ENGINES & DATA HANDLING (SUPABASE)
# ==========================================
conn = st.connection("supabase", type="sql")

COUNTRIES = ["Spain", "Mexico", "Poland", "Germany", "Italy", "Brazil", "Colombia", "Turkey", "Argentina", "Peru", "Chile"]
COUNTRY_MAPPING = {"Spain": "ES", "Mexico": "MX", "Poland": "PL", "Germany": "DE", "Italy": "IT", "Brazil": "BR", "Colombia": "CO", "Turkey": "TR", "Argentina": "AR", "Peru": "PE", "Chile": "CL"}

@st.cache_data(ttl=600)
def fetch_google_roster():
    try: return pd.read_csv("https://docs.google.com/spreadsheets/d/1trEEVG1Z_7g5ySyG0XzCJ4MYNC4jWN3_GFXX_TJjgdw/export?format=csv&gid=0")
    except: return pd.DataFrame()

def get_active_agents_for_country(country_name, return_dicts=False):
    df = fetch_google_roster()
    if df.empty: return []
    cols = {str(c).lower().strip(): c for c in df.columns}
    c_col, n_col, r_col = cols.get('country'), cols.get('name', cols.get('agent')), cols.get('role')
    e_col, t_col = cols.get('end date', cols.get('end_date')), cols.get('team')

    if not (c_col and n_col): return []
    mapped_ctry = COUNTRY_MAPPING.get(country_name, country_name)
    df_f = df[df[c_col].astype(str).str.contains(f"{country_name}|{mapped_ctry}", case=False, na=False)]
    
    if r_col: df_f = df_f[df_f[r_col].astype(str).str.contains("CC agent", case=False, na=False)]
    if e_col: df_f = df_f[df_f[e_col].isna() | (df_f[e_col].astype(str).str.strip() == '') | (df_f[e_col].astype(str).str.lower() == 'nan')]
        
    if return_dicts:
        return sorted([{'Name': str(row[n_col]), 'Team': 'hc' if t_col and 'hc' in str(row[t_col]).strip().lower() else 'support'} for _, row in df_f.iterrows()], key=lambda x: x['Name'])
    return sorted(df_f[n_col].dropna().unique().tolist())

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
    while calculate_erlang_c(vol, aht, target_time, agents) < target_sl and agents < 1000: agents += 1
    return agents

def aggregate_wfm(df, group_cols):
    if df.empty: return df
    def w_avg(d, col, w_col): return np.average(d[col], weights=d[w_col]) if d[w_col].sum() > 0 else d[col].mean()
    return df.groupby(group_cols).apply(lambda x: pd.Series({'Volume': x['Volume'].sum(), 'FTE': x.get('FTE', pd.Series([0])).mean(), 'SLA': w_avg(x, 'SLA', 'Volume') if 'SLA' in x.columns else 0.80, 'AHT': w_avg(x, 'AHT', 'Volume') if 'AHT' in x.columns else 300})).reset_index()

def generate_time_slots(): return [f"{str(h).zfill(2)}:{str(m).zfill(2)}" for h in range(0, 24) for m in (0, 30)]

def update_exc_status(agent, date, stime, status, msg):
    """Helper to approve/reject exceptions efficiently."""
    try:
        with conn.engine.connect() as c:
            c.execute(text('UPDATE exception_logs SET "Status" = :stat WHERE "Agent" = :agt AND "Date" = :dt AND "Start Time" = :stm'), {"stat": status, "agt": agent, "dt": date, "stm": stime})
            c.commit()
        st.success(msg)
        sync_from_cloud()
        st.rerun()
    except Exception as e: st.error(f"DB Error: {e}")

def sync_from_cloud():
    try:
        st.session_state.user_db = conn.query("SELECT * FROM user_db;", ttl="0m")
        md = conn.query("SELECT * FROM master_data;", ttl="0m")
        if not md.empty and 'Date' in md.columns:
            dt_series = pd.to_datetime(md['Date'], errors='coerce')
            md['Time'], md['Date'] = dt_series.dt.strftime('%H:%M'), dt_series.dt.date.astype(str)
        st.session_state.master_data = md
        
        st.session_state.exception_logs = conn.query("SELECT * FROM exception_logs;", ttl="0m")
        if 'Status' not in st.session_state.exception_logs.columns: st.session_state.exception_logs['Status'] = 'Approved'
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

client_id, client_secret, redirect_uri = st.secrets.get("google_auth", {}).get("client_id", ""), st.secrets.get("google_auth", {}).get("client_secret", ""), st.secrets.get("google_auth", {}).get("redirect_uri", "")

if not st.session_state.logged_in and "code" in st.query_params:
    try:
        token_data = requests.post("https://oauth2.googleapis.com/token", data={"code": st.query_params["code"], "client_id": client_id, "client_secret": client_secret, "redirect_uri": redirect_uri, "grant_type": "authorization_code"}).json()
        if "id_token" in token_data:
            email = id_token.verify_oauth2_token(token_data["id_token"], google.auth.transport.requests.Request(), client_id).get("email")
            user_match = st.session_state.user_db[st.session_state.user_db['email'].str.lower() == email.lower()]
            if not user_match.empty:
                st.session_state.logged_in, st.session_state.user_role, st.session_state.current_email = True, str(user_match.iloc[0]['role']), email
                st.query_params.clear()
                st.rerun()
            else: st.error(f"Access Denied: {email} not authorized."); st.stop()
        else: st.error(f"Token Error: {token_data}"); st.stop()
    except Exception as e: st.error(f"Auth Error: {e}")

if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True); st.image("https://www.docplanner.com/img/logo-default-group-en.svg", width=180); st.title("Workforce Workspace")
        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?client_id={client_id}&redirect_uri={urllib.parse.quote(redirect_uri, safe='')}&response_type=code&scope=openid%20email%20profile&prompt=consent"
        st.markdown(f'<a href="{auth_url}" target="_blank" style="text-decoration:none;"><div style="background:white;color:#757575;border:1px solid #dadce0;border-radius:4px;padding:12px;text-align:center;font-weight:500;display:flex;align-items:center;justify-content:center;box-shadow:0 2px 4px rgba(0,0,0,0.1);"><img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" style="width:18px;margin-right:10px;">Sign in with Google</div></a>', unsafe_allow_html=True)
    st.stop()

# ==========================================
# 4. GLOBAL ASSETS & NAVIGATION
# ==========================================
nav_icons = {"Dashboard": "⟢", "Import Data": "⤓", "Forecasting": "📈", "Scheduling": "📅", "Exception Management": "⚠", "Capacity Planner (Erlang)": "◈", "Reporting Center": "▤", "Admin Panel": "⚙", "System Status": "🛡", "Agent Portal": "👤", "Real-Time Ops": "📡"}
role = st.session_state.user_role
menu_options = ["Dashboard", "Import Data", "Forecasting", "Scheduling", "Exception Management", "Capacity Planner (Erlang)", "Reporting Center", "Real-Time Ops", "Admin Panel", "System Status"] if role == "Admin" else (["Dashboard", "Forecasting", "Scheduling", "Exception Management", "Capacity Planner (Erlang)", "Real-Time Ops"] if role == "Manager" else ["Agent Portal"])

with st.sidebar:
    st.image("https://www.docplanner.com/img/logo-default-group-en.svg", width=130); st.markdown(f"**{st.session_state.current_email}**"); st.caption(f"Role: {role}")
    ui_divider()
    menu = st.radio("Navigation", menu_options, label_visibility="collapsed")
    ui_divider()
    selected_markets = st.multiselect("Select Markets", COUNTRIES, default=COUNTRIES) if role in ["Admin", "Manager"] and st.radio("View Setting", ["Global", "Regional Select"]) == "Regional Select" else COUNTRIES
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Sync Data 🔄", use_container_width=True): sync_from_cloud(); st.rerun()
    if st.button("Log Out 🚪", use_container_width=True): st.session_state.logged_in = False; st.rerun()

def render_header(title): st.markdown(f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;"><span style="font-size:1.6rem;color:{DP_TEAL};opacity:0.8;">{nav_icons.get(title, "⟢")}</span><h1 style="margin:0 !important;">{title}</h1></div>', unsafe_allow_html=True)

# ==========================================
# 5. MAIN MODULES
# ==========================================
if menu == "Dashboard":
    render_header("Executive Dashboard")
    st.write("### 🔍 Dashboard Filters")
    fc1, fc2 = st.columns(2)
    dash_markets = fc1.multiselect("Filter Target Markets", COUNTRIES, default=selected_markets)
    dash_agents = fc2.multiselect("Filter Specific Agents (For Adherence Only)", sorted([a for m in dash_markets for a in get_active_agents_for_country(m, False)]))
    ui_divider("20px")
    
    st.write("### Volume & Performance Overview")
    df = st.session_state.master_data
    if not df.empty and 'Country' in df.columns:
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df_f = df[df['Country'].isin(dash_markets)].copy()
        if not df_f.empty:
            for c in ['Volume', 'SLA', 'AHT', 'FTE']: df_f[c] = pd.to_numeric(df_f.get(c, 0), errors='coerce').fillna(0)
            tot_v, avg_fte = df_f['Volume'].sum(), df_f['FTE'].mean()
            sl_w = np.average(df_f['SLA'], weights=df_f['Volume']) if tot_v > 0 else 0.80
            aht_w = np.average(df_f['AHT'], weights=df_f['Volume']) if tot_v > 0 else 300
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Volume", f"{tot_v:,.0f}"); c2.metric("Weighted SLA%", f"{sl_w*100:.1f}%")
            c3.metric("Weighted AHT", f"{int(aht_w)}s"); c4.metric("Average FTE", f"{avg_fte:,.1f}")
            st.plotly_chart(px.area(aggregate_wfm(df_f, [df_f['Date'].dt.date, 'Channel']), x='Date', y='Volume', color='Channel', title="Volume Demand by Channel", template="plotly_white"), use_container_width=True)
        else: st.info("No historical data matches the selected market filters.")
    else: st.info("Cloud database is empty.")

    ui_divider("20px")
    st.write("### Adherence to Schedule (%)")
    st.caption("*(Calculated dynamically: Time Scheduled vs Time impacted by Exceptions)*")
    
    s_db, e_db = st.session_state.schedule_db, st.session_state.exception_logs
    if not s_db.empty and 'Country' in s_db.columns:
        sch_adh = s_db[s_db['Country'].isin(dash_markets)].copy()
        if dash_agents: sch_adh = sch_adh[sch_adh['Agent'].isin(dash_agents)]
        sch_adh = sch_adh[~sch_adh['Base_Activity'].isin(["-", "Off", "Lunch"])]
        
        if not sch_adh.empty:
            merged_adh = sch_adh
            if not e_db.empty and 'Status' in e_db.columns:
                merged_adh = sch_adh.merge(e_db[e_db['Status'] == 'Approved'][['Agent', 'Date', 'Start Time', 'Type']], left_on=['Agent', 'Date', 'Time'], right_on=['Agent', 'Date', 'Start Time'], how='left')
                merged_adh['Has_Exception'] = merged_adh['Type'].notna().astype(int)
            else: merged_adh['Has_Exception'] = 0

            agent_daily = merged_adh.groupby(['Date', 'Agent']).agg(Scheduled_Intervals=('Time', 'count'), Exception_Intervals=('Has_Exception', 'sum')).reset_index()
            agent_daily['Adherence'] = ((agent_daily['Scheduled_Intervals'] - agent_daily['Exception_Intervals']) / agent_daily['Scheduled_Intervals']) * 100
            
            fig_adh = px.line(agent_daily, x='Date', y='Adherence', color='Agent', title="Agent-Level Adherence %", template="plotly_white", markers=True) if dash_agents else px.line(agent_daily.groupby('Date')['Adherence'].mean().reset_index(), x='Date', y='Adherence', title="Market Average Adherence %", template="plotly_white", markers=True)
            fig_adh.update_yaxes(range=[0, 105]); st.plotly_chart(fig_adh, use_container_width=True)
        else: st.info("No active work shifts found for the selected agents.")
    else: st.info("Schedule database is empty.")

elif menu == "Import Data":
    render_header("Data Ingestion & Aggregation")
    st.write("### 1. Upload Raw Historical Data"); st.markdown("System automatically parses timestamps to 30-min blocks & prepares Erlang data.")
    up = st.file_uploader("Drop Market CSV File", type="csv")
    if up:
        with st.spinner("Processing intervals..."):
            raw_df = pd.read_csv(up)
            missing = [c for c in ['date_timestamp', 'country', 'channel', 'aht_minutes', 'case_id'] if c not in raw_df.columns]
            if not missing:
                raw_df['date_timestamp'] = pd.to_datetime(raw_df['date_timestamp'], errors='coerce')
                raw_df['Date'] = raw_df.dropna(subset=['date_timestamp'])['date_timestamp'].dt.floor('30min').dt.strftime('%Y-%m-%d %H:%M:%S')
                agg_df = raw_df.groupby(['Date', 'country', 'channel']).agg(Volume=('case_id', 'count'), AHT=('aht_minutes', lambda x: x.mean() * 60)).reset_index().rename(columns={'country': 'Country', 'channel': 'Channel'})
                agg_df['SLA'], agg_df['FTE'] = 0.80, 0.0
                st.write("### Ready for Database"); st.dataframe(agg_df.head(5))
                if st.button("Commit to Supabase"):
                    try: agg_df.to_sql('master_data', con=conn.engine, if_exists='append', index=False); st.success("Committed!"); sync_from_cloud()
                    except Exception as e: st.error(f"DB Error: {e}")
            else: st.error(f"Upload Failed: Missing columns: {missing}")

elif menu == "Forecasting":
    render_header("12-Month Advanced Forecasting & Shift Generator")
    df = st.session_state.master_data.copy()
    if not df.empty and 'Country' in df.columns:
        c1, c2 = st.columns(2)
        if role == "Admin":
            with c1:
                target_country = st.selectbox("Select Country", sorted(df['Country'].unique()))
                shrinkage_factor = st.slider(f"Expected Shrinkage %", 0, 80, 30) / 100.0
                if st.button(f"🚀 Generate 90-Day Plan for {target_country}"):
                    with st.spinner("Running Shift Engine..."):
                        agent_dicts = get_active_agents_for_country(target_country, True)
                        if not agent_dicts: st.error("⚠️ 0 active CC agents found."); st.stop()
                        
                        cdf = df[df['Country'] == target_country].copy()
                        cdf['Date'] = pd.to_datetime(cdf['Date'], errors='coerce')
                        cdf['DoW'], cdf['Weight'] = cdf['Date'].dt.dayofweek, 0.5 ** (datetime.now() - cdf['Date']).dt.days.clip(lower=0) / 30.0
                        
                        def c_wght(x): return pd.Series({'Volume': np.average(x['Volume'].fillna(0), weights=x['Weight']), 'AHT': np.average(x['AHT'].fillna(300), weights=x['Weight'])}) if x['Weight'].sum() > 0 else pd.Series({'Volume': x['Volume'].mean(), 'AHT': x['AHT'].mean()})
                        baseline = cdf.groupby(['Country', 'Channel', 'DoW', 'Time']).apply(c_wght).reset_index()
                        
                        f_rows, s_rows, intervals = [], [], generate_time_slots()
                        agent_sch = {ag['Name']: {'Team': ag['Team'], 'Start': f"{8+(i%4):02d}:00", 'End': f"{8+(i%4)+9:02d}:00", 'L_S': f"{8+(i%4)+4:02d}:00", 'L_E': f"{8+(i%4)+5:02d}:00", 'Grid': {}, 'Prev': "-"} for i, ag in enumerate(agent_dicts)}
                        
                        for d in pd.date_range(datetime.now().date() + timedelta(days=1), periods=90):
                            dbase = baseline[baseline['DoW'] == d.dayofweek]
                            reqs = {t: {"Phone & Cases": 0, "Chat": 0, "Whatsapp": 0, "Cases": 0} for t in intervals}
                            
                            for _, r in dbase.iterrows():
                                v, a, c_lower = r.get('Volume', 50), r.get('AHT', 300), str(r['Channel']).lower()
                                conc, act = (3, "Chat") if 'chat' in c_lower else ((5, "Whatsapp") if 'whatsapp' in c_lower else (1, "Cases" if 'email' in c_lower or 'cases' in c_lower else "Phone & Cases"))
                                req_fte = math.ceil((get_required_fte(v, a, 0.80) / conc) / (1 - shrinkage_factor))
                                reqs[r['Time']][act] += req_fte
                                f_rows.append({"Date": d.strftime('%Y-%m-%d'), "Time": r['Time'], "Country": r['Country'], "Channel": r['Channel'], "Forecast_Volume": v, "Req_FTE": req_fte})

                            for ag, data in agent_sch.items():
                                in_shift = False
                                for t in intervals:
                                    if t == data['Start']: in_shift = True
                                    if t == data['End']: in_shift = False
                                    data['Grid'][t] = "Lunch" if in_shift and data['L_S'] <= t < data['L_E'] else ("Available" if in_shift else "Off")
                            
                            for t in intervals:
                                av_ag = [ag for ag, d in agent_sch.items() if d['Grid'][t] == "Available"]
                                for act in ["Phone & Cases", "Chat", "Whatsapp", "Cases"]:
                                    if reqs[t][act] <= 0: continue
                                    sk = [a for a in av_ag if agent_sch[a]['Team'] == ('support' if act == "Phone & Cases" else ('hc' if act in ["Chat", "Whatsapp"] else agent_sch[a]['Team']))]
                                    sk.sort(key=lambda a: 0 if agent_sch[a]['Prev'] == act else 1)
                                    for a in sk[:reqs[t][act]]: agent_sch[a]['Grid'][t], agent_sch[a]['Prev'] = act, act; av_ag.remove(a)
                                for a in av_ag: agent_sch[a]['Grid'][t], agent_sch[a]['Prev'] = "-", "-"
                                    
                            for ag, data in agent_sch.items():
                                for t in intervals: s_rows.append({"Country": target_country, "YearMonth": d.strftime('%Y-%m'), "Date": d.strftime('%Y-%m-%d'), "Time": t, "Agent": ag, "Base_Activity": data['Grid'][t]})
                        
                        try:
                            with conn.engine.connect() as c:
                                c.execute(text('DELETE FROM forecast_db WHERE "Country" = :ctry'), {"ctry": target_country})
                                c.execute(text('DELETE FROM schedule_db WHERE "Country" = :ctry'), {"ctry": target_country})
                                c.commit()
                            pd.DataFrame(f_rows).to_sql('forecast_db', con=conn.engine, if_exists='append', index=False)
                            pd.DataFrame(s_rows).to_sql('schedule_db', con=conn.engine, if_exists='append', index=False)
                            st.success(f"Generated plan for {target_country}!"); sync_from_cloud()
                        except Exception as e: st.error(f"DB Error: {e.split('LINE 1')[0] if 'LINE 1' in str(e) else e}")
        
        f_db = st.session_state.forecast_db
        if not f_db.empty and 'Country' in f_db.columns:
            ui_divider("20px")
            vc = st.selectbox("View Forecast For:", sorted(f_db['Country'].unique()))
            fd = f_db[f_db['Country'] == vc].groupby(['Date'])['Forecast_Volume'].sum().reset_index()
            st.plotly_chart(px.line(fd, x='Date', y='Forecast_Volume', title=f"Forecast ({vc})", template="plotly_white"), use_container_width=True)

elif menu == "Scheduling":
    render_header("Master Scheduling & Roster")
    s_db, e_db = st.session_state.schedule_db, st.session_state.exception_logs
    if not s_db.empty and 'Country' in s_db.columns:
        c1, c2, c3 = st.columns([1, 1, 2])
        market_db = s_db[s_db['Country'] == c1.selectbox("Select Market", sorted(s_db['Country'].unique()))].copy()
        if not market_db.empty and 'Date' in market_db.columns:
            day_sch = market_db[market_db['Date'] == c2.selectbox("Select Date", sorted(market_db['Date'].unique()))].copy()
            if not e_db.empty and 'Date' in e_db.columns:
                merged = day_sch.merge(e_db[e_db['Status'] == 'Approved'][['Agent', 'Start Time', 'Type']], left_on=['Agent', 'Time'], right_on=['Agent', 'Start Time'], how='left')
                merged['Live_Status'] = merged['Type'].fillna(merged['Base_Activity'])
                final_df = merged[['Agent', 'Time', 'Live_Status']]
            else: final_df = day_sch[['Agent', 'Time', 'Base_Activity']].rename(columns={'Base_Activity': 'Live_Status'})
            
            if 'Time' in final_df.columns: st.dataframe(final_df.pivot_table(index='Agent', columns='Time', values='Live_Status', aggfunc='first').fillna("-").sort_index(axis=1), use_container_width=True)
            else: st.info("Time column missing.")
        else: st.info("No data for market.")
    else: st.info("Database empty.")

elif menu == "Exception Management":
    render_header("Exception Workflows")
    tab1, tab2 = st.tabs(["📋 Approval Queue", "➕ Direct Log (Admin/Manager)"])
    with tab1:
        exc_db = st.session_state.exception_logs
        if not exc_db.empty and 'Status' in exc_db.columns:
            pending = exc_db[exc_db['Status'] == 'Pending']
            for idx, r in pending.iterrows():
                with st.expander(f"🔴 Request from {r['Agent']} on {r['Date']}"):
                    st.write(f"**Type:** {r['Type']} | **Time:** {r['Start Time']} | **Notes:** {r['Notes']}")
                    colA, colB = st.columns(2)
                    if colA.button("✅ Approve", key=f"a_{idx}"): update_exc_status(r['Agent'], r['Date'], r['Start Time'], 'Approved', "Approved.")
                    if colB.button("❌ Reject", key=f"r_{idx}"): update_exc_status(r['Agent'], r['Date'], r['Start Time'], 'Rejected', "Rejected.")
            st.write("### Processed"); st.dataframe(exc_db[exc_db['Status'] != 'Pending'], use_container_width=True)
        else: st.info("No exceptions logged.")

    with tab2:
        ct_in = st.selectbox("Market Selection", COUNTRIES)
        active_agents = get_active_agents_for_country(ct_in)
        with st.form("exc_log_direct", clear_on_submit=True):
            c1, c2 = st.columns(2)
            exc_date, exc_time = c1.date_input("Date"), c2.selectbox("Start Time", generate_time_slots())
            agt_in = st.selectbox("Staff Name", active_agents) if active_agents else st.text_input("Staff Name (No agents found)")
            t_in, d_in = st.selectbox("Reason Code", list(STATUS_DICT.keys())), st.number_input("Duration (Min)", 30, step=30)
            if st.form_submit_button("Force Log"):
                if agt_in:
                    try: pd.DataFrame([[ct_in, exc_date.strftime("%Y-%m-%d"), exc_time, agt_in, t_in, d_in, "Override", "Approved"]], columns=["Country", "Date", "Start Time", "Agent", "Type", "Duration (Min)", "Notes", "Status"]).to_sql('exception_logs', con=conn.engine, if_exists='append', index=False); st.success("Logged!"); sync_from_cloud()
                    except Exception as e: st.error(f"DB error: {e}")
                else: st.error("Valid name required.")

elif menu == "Capacity Planner (Erlang)":
    render_header("Capacity & Headcount Plan Drill-Down")
    f_db, s_db = st.session_state.forecast_db, st.session_state.schedule_db
    if f_db.empty or s_db.empty: st.info("Databases must be populated.")
    else:
        view_scale = st.radio("Aggregation", ["Daily Overview", "Hourly Drill-Down"], horizontal=True)
        f_m, s_m = f_db[f_db['Country'].isin(selected_markets)], s_db[s_db['Country'].isin(selected_markets)]
        if view_scale == "Daily Overview" and 'Date' in f_m.columns:
            demand = f_m.groupby('Date')['Req_FTE'].max().reset_index()
            supply = s_m[~s_m['Base_Activity'].isin(["-", "Off", "Lunch"])].groupby('Date')['Agent'].nunique().reset_index(name='Scheduled_FTE')
            gap = demand.merge(supply, on='Date', how='outer').fillna(0)
            gap['Variance'] = gap['Scheduled_FTE'] - gap['Req_FTE']
            st.plotly_chart(px.bar(gap, x='Date', y='Variance', color=np.where(gap['Variance'] < 0, 'Understaffed', 'Overstaffed'), color_discrete_map={'Understaffed':'#ef4444', 'Overstaffed':'#10b981'}), use_container_width=True)
        elif 'Date' in f_m.columns and f_m['Date'].nunique() > 0:
            sel_date = st.selectbox("Select Date", sorted(f_m['Date'].unique()))
            demand = f_m[f_m['Date'] == sel_date].groupby('Time')['Req_FTE'].sum().reset_index()
            supply = s_m[(s_m['Date'] == sel_date) & (~s_m['Base_Activity'].isin(["-", "Off", "Lunch"]))].groupby('Time')['Agent'].count().reset_index(name='Scheduled_FTE')
            gap = demand.merge(supply, on='Time', how='outer').fillna(0).sort_values(by='Time')
            gap['Variance'] = gap['Scheduled_FTE'] - gap['Req_FTE']
            st.plotly_chart(go.Figure(go.Bar(x=gap['Time'], y=gap['Variance'], marker_color=np.where(gap['Variance'] < 0, '#ef4444', '#10b981'))).update_layout(template="plotly_white", title="Variance by Interval"), use_container_width=True)

elif menu == "Real-Time Ops":
    render_header("Live Command Center")
    st.warning("⚠️ INTEGRATION STATUS: Placeholder mode. Awaiting API Webhooks.")
    c1, c2 = st.columns(2); c1.bar_chart(np.random.randint(0, 10, 12), color=DP_NAVY); c2.line_chart(np.random.randint(20, 120, 12), color=DP_TEAL)

elif menu == "Admin Panel":
    render_header("Access Management & Documentation")
    t1, t2 = st.tabs(["⚙️ Access Control", "📘 Operations Manual"])
    with t1:
        with st.form("user_add", clear_on_submit=True):
            n_e, n_r = st.text_input("Email"), st.selectbox("Role", ["Admin", "Manager", "User"])
            if st.form_submit_button("Provision Access") and n_e:
                try: pd.DataFrame([{"email": n_e, "password": "sso", "role": n_r}]).to_sql('user_db', con=conn.engine, if_exists='append', index=False); st.success("Granted!"); sync_from_cloud()
                except Exception as e: st.error(f"DB Error: {e}")
        st.dataframe(st.session_state.user_db[['email', 'role']], use_container_width=True)
    with t2: st.markdown("### WFM Master Guide"); st.dataframe(pd.DataFrame(list(STATUS_DICT.items()), columns=['Status', 'Guidelines']), use_container_width=True, hide_index=True)

elif menu == "Agent Portal":
    render_header("My Agent Portal")
    s_db, e_db = st.session_state.schedule_db, st.session_state.exception_logs
    if not s_db.empty and 'Agent' in s_db.columns:
        my_sch = s_db[s_db['Agent'].str.lower() == st.session_state.current_email.lower()].copy()
        if not my_sch.empty:
            view_df = my_sch[['Date', 'Time', 'Base_Activity']].rename(columns={'Base_Activity': 'Live_Status'})
            if not e_db.empty:
                my_exc = e_db[(e_db['Agent'].str.lower() == st.session_state.current_email.lower()) & (e_db['Status'] == 'Approved')]
                merged = my_sch.merge(my_exc[['Date', 'Start Time', 'Type']], left_on=['Date', 'Time'], right_on=['Date', 'Start Time'], how='left')
                view_df['Live_Status'] = merged['Type'].fillna(merged['Base_Activity'])
            st.dataframe(view_df.pivot_table(index='Date', columns='Time', values='Live_Status', aggfunc='first').fillna("-").sort_index(axis=1), use_container_width=True)
        else: st.warning("No schedule records found.")
    
    ui_divider("20px")
    st.write("### ⚠️ Submit Exception Request")
    with st.form("agent_exc_request", clear_on_submit=True):
        c1, c2 = st.columns(2)
        exc_date, exc_time = c1.date_input("Date"), c2.selectbox("Time", generate_time_slots())
        t_in, d_in, n_in = st.selectbox("Reason", list(STATUS_DICT.keys())), st.number_input("Duration (Min)", 30, step=30), st.text_input("Notes")
        if st.form_submit_button("Send"):
            try: pd.DataFrame([["Global", exc_date.strftime("%Y-%m-%d"), exc_time, st.session_state.current_email, t_in, d_in, n_in, "Pending"]], columns=["Country", "Date", "Start Time", "Agent", "Type", "Duration (Min)", "Notes", "Status"]).to_sql('exception_logs', con=conn.engine, if_exists='append', index=False); st.success("Sent!"); sync_from_cloud()
            except Exception as e: st.error(f"Failed: {e}")

elif menu == "Reporting Center":
    render_header("Data Exports")
    if not st.session_state.master_data.empty: st.download_button("Export CSV", data=st.session_state.master_data.to_csv(index=False).encode('utf-8'), file_name="WFM.csv", mime="text/csv")
    else: st.warning("No data.")

elif menu == "System Status":
    render_header("Infrastructure Health")
    c1, c2, c3 = st.columns(3)
    c1.metric("Database", "Supabase"); c2.metric("Rows", len(st.session_state.master_data)); c3.metric("Latency", "< 5ms")
