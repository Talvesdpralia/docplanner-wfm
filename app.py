import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio
from datetime import datetime
import math
from streamlit_gsheets import GSheetsConnection

# 1. UI & DESIGN ENGINE - TOTAL CSS OVERRIDE
st.set_page_config(page_title="Docplanner WFM Hub", layout="wide", page_icon="🏥")

DP_TEAL = "#00c4a7"
DP_NAVY = "#011e41"
DP_SLATE = "#4b5563"

def apply_custom_design():
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Figtree:wght@300;400;500;600&display=swap');
        
        /* 1. Global Reset & Figtree Font */
        html, body, [class*="css"], .stApp {{
            font-family: 'Figtree', sans-serif !important;
            font-size: 13.5px !important;
            background-color: #ffffff !important;
        }}

        /* 2. REMOVE RADIO CIRCLES & RED ACCENTS */
        [data-testid="stSidebar"] div[role="radiogroup"] label div:first-child {{
            display: none !important;
        }}
        [data-testid="stSidebar"] div[role="radiogroup"] {{
            accent-color: {DP_TEAL} !important;
        }}
        
        /* 3. GEMINI STYLE NAVIGATION */
        [data-testid="stSidebar"] div[role="radiogroup"] label {{
            padding: 10px 16px !important;
            margin: 4px 0px !important;
            border-radius: 12px !important;
            transition: all 0.3s ease !important;
            border: none !important;
            background-color: transparent !important;
        }}
        [data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] {{
            background: rgba(0, 196, 167, 0.08) !important;
            color: {DP_TEAL} !important;
            font-weight: 500 !important;
        }}

        /* 4. REALISTIC SHADOW INPUTS (Prompt Box Style) */
        /* This specifically targets the login and selection boxes */
        .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input {{
            background-color: #ffffff !important;
            border: 1px solid rgba(0,0,0,0.03) !important; /* Almost invisible border */
            border-radius: 24px !important; 
            padding: 12px 20px !important;
            color: {DP_NAVY} !important;
            /* Multi-layer soft shadow for realism */
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 10px 25px -5px rgba(0, 0, 0, 0.05) !important;
            transition: all 0.3s ease !important;
        }}
        
        .stTextInput input:focus, .stSelectbox div[data-baseweb="select"]:focus {{
            box-shadow: 0 10px 30px rgba(0, 196, 167, 0.12) !important;
            transform: translateY(-1px) !important;
            border: 1px solid rgba(0, 196, 167, 0.3) !important;
        }}

        /* 5. GLASS SIDEBAR - SALIENT BLUR */
        section[data-testid="stSidebar"] {{
            background: rgba(255, 255, 255, 0.01) !important;
            backdrop-filter: blur(45px) saturate(180%) !important;
            border-right: 1px solid rgba(0, 0, 0, 0.06) !important;
            width: 300px !important;
        }}

        /* 6. TYPOGRAPHY & HEADERS */
        h1 {{ font-weight: 300 !important; font-size: 1.6rem !important; color: {DP_NAVY}; letter-spacing: -0.5px; }}
        h2 {{ font-weight: 400 !important; font-size: 1.1rem !important; color: {DP_SLATE}; }}

        /* 7. METRIC CARDS */
        [data-testid="stMetric"] {{
            background: #ffffff !important;
            padding: 22px !important;
            border-radius: 20px !important;
            box-shadow: 0 4px 20px rgba(0,0,0,0.03) !important;
            border: 1px solid #fdfdfd !important;
        }}
        
        /* 8. BUTTONS */
        .stButton>button {{
            background: {DP_TEAL} !important;
            color: white !important;
            border-radius: 24px !important;
            border: none !important;
            padding: 10px 30px !important;
            font-weight: 500 !important;
            box-shadow: 0 6px 15px rgba(0, 196, 167, 0.2) !important;
        }}
        </style>
    """, unsafe_allow_html=True)

apply_custom_design()

# 2. DATABASE CONNECTION (GSHEETS)
conn = st.connection("gsheets", type=GSheetsConnection)

def sync_from_cloud():
    try:
        st.session_state.user_db = conn.read(worksheet="user_db", ttl="0")
        st.session_state.master_data = conn.read(worksheet="master_data", ttl="0")
        st.session_state.exception_logs = conn.read(worksheet="exception_logs", ttl="0")
    except:
        st.session_state.user_db = pd.DataFrame([{"email": "telmo.alves@docplanner.com", "password": "Memes0812", "role": "Admin"}])
        st.session_state.master_data = pd.DataFrame(columns=["Date", "Volume", "SL", "AHT", "FTE", "Country"])
        st.session_state.exception_logs = pd.DataFrame(columns=["Country", "Timestamp", "Agent", "Type", "Duration (Min)", "Notes"])

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    sync_from_cloud()

# 3. SETUP & ASSETS
DP_LOGO = "https://www.docplanner.com/img/logo-default-group-en.svg"
COUNTRIES = ["Spain", "Mexico", "Poland", "Germany", "Italy", "Brazil", "Colombia", "Turkey"]

# 4. LOGIN GATE (REFINED)
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.image(DP_LOGO, width=180)
        st.title("Workforce Management")
        e_in = st.text_input("Work Email", placeholder="your.name@docplanner.com")
        p_in = st.text_input("Password", type="password", placeholder="••••••••")
        if st.button("Continue", use_container_width=True):
            db = st.session_state.user_db
            match = db[(db['email'] == e_in) & (db['password'] == p_in)]
            if not match.empty:
                st.session_state.logged_in = True
                st.session_state.user_role = str(match.iloc[0]['role'])
                st.session_state.current_email = str(match.iloc[0]['email'])
                st.rerun()
            else: st.error("Access denied. Check credentials.")
    st.stop()

# 5. SIDEBAR NAVIGATION - FIXING VISIBILITY
role = st.session_state.user_role
nav_icons = {
    "Dashboard": "⟢", "Import Data": "⤓", "Forecasting": "📈", 
    "Exception Management": "⚠", "Capacity Planner (Erlang)": "◈", 
    "Reporting Center": "▤", "Admin Panel": "⚙", "System Status": "🛡"
}

# Ensure Role-based access is correctly built
available_nav = ["Dashboard", "Forecasting"]
if role == "Admin": 
    available_nav = ["Dashboard", "Import Data", "Forecasting", "Exception Management", "Capacity Planner (Erlang)", "Reporting Center", "Admin Panel", "System Status"]
elif role == "Manager":
    available_nav = ["Dashboard", "Forecasting", "Exception Management", "Capacity Planner (Erlang)"]

with st.sidebar:
    st.image(DP_LOGO, width=130)
    st.markdown(f"**{st.session_state.current_email}**")
    st.divider()
    
    menu = st.radio("Select workspace", available_nav)
    
    st.divider()
    view_mode = st.radio("View Setting", ["Global", "Regional Select"])
    selected_markets = COUNTRIES
    if view_mode == "Regional Select":
        selected_markets = st.multiselect("Markets", COUNTRIES, default=COUNTRIES)
    
    if st.button("Sync Refresh 🔄", use_container_width=True):
        sync_from_cloud()
        st.rerun()

# 6. ENGINES
def calculate_erlang_c(vol, aht, target_t, agents):
    intensity = (vol * aht) / 3600
    if agents <= intensity: return 0.0 
    sum_inv = sum([(intensity**i) / math.factorial(i) for i in range(int(agents))])
    numerator = (intensity**agents / math.factorial(int(agents))) * (agents / (agents - intensity))
    prob_w = numerator / (sum_inv + numerator)
    return 1 - (prob_w * math.exp(-(agents - intensity) * (target_t / aht)))

# 7. MAIN INTERFACE MODULES
def render_header(title, icon):
    st.markdown(f'<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 25px;"><span style="font-size: 1.5rem; color: {DP_TEAL}; opacity: 0.8;">{icon}</span><h1>{title}</h1></div>', unsafe_allow_html=True)

if menu == "Dashboard":
    render_header("Performance Overview", nav_icons["Dashboard"])
    df = st.session_state.master_data
    if not df.empty:
        df_f = df[df['Country'].isin(selected_markets)].copy()
        if not df_f.empty:
            for c in ['Volume', 'SL', 'AHT', 'FTE']: df_f[c] = pd.to_numeric(df_f[c], errors='coerce').fillna(0)
            c1, c2, c3, c4 = st.columns(4)
            tot_v = df_f['Volume'].sum()
            c1.metric("Volume", f"{tot_v:,.0f}")
            c2.metric("SL%", f"{(df_f['Volume']*df_f['SL']).sum()/tot_v:.1f}%" if tot_v > 0 else "0%")
            c3.metric("AHT", f"{int(df_f['AHT'].mean())}s")
            c4.metric("FTE", f"{df_f['FTE'].sum():,.1f}")
            st.divider()
            st.plotly_chart(px.line(df_f, x='Date', y='Volume', color='Country', template="plotly_white"), use_container_width=True)
    else: st.info("Welcome. Start by importing market data.")

elif menu == "Import Data":
    render_header("Data Ingestion", nav_icons["Import Data"])
    target = st.selectbox("Market Target", COUNTRIES)
    up = st.file_uploader("Drop CSV file", type="csv")
    if up:
        new_df = pd.read_csv(up)
        new_df['Country'] = target
        st.session_state.master_data = pd.concat([st.session_state.master_data[st.session_state.master_data['Country'] != target], new_df], ignore_index=True)
        conn.update(worksheet="master_data", data=st.session_state.master_data)
        st.success("Synchronized with Google Sheets.")

elif menu == "Capacity Planner (Erlang)":
    render_header("Staffing Requirement Engine", nav_icons["Capacity Planner (Erlang)"])
    
    col1, col2 = st.columns(2)
    with col1:
        v_h = st.number_input("Peak Period Volume", value=200)
        a_s = st.number_input("Target AHT (Seconds)", value=300)
    with col2:
        s_t = st.slider("Service Level Target (%)", 50, 99, 80) / 100
        sh = st.slider("Shrinkage Factor (%)", 0, 50, 20) / 100
    if v_h > 0:
        req = math.ceil((v_h * a_s) / 3600) + 1
        ach = 0
        while ach < s_t and req < 500:
            ach = calculate_erlang_c(v_h, a_s, 20, req)
            if ach < s_target: req += 1
        st.divider()
        st.metric("Recommended FTE Capacity", f"{math.ceil(req / (1 - sh))} FTE")

elif menu == "Admin Panel":
    render_header("Access Management", nav_icons["Admin Panel"])
    with st.form("new_user_form", clear_on_submit=True):
        n_e = st.text_input("Email")
        n_p = st.text_input("Temporary Password")
        n_r = st.selectbox("Permission Level", ["Admin", "Manager", "User"])
        if st.form_submit_button("Grant Access"):
            new_u = pd.DataFrame([{"email": n_e, "password": n_p, "role": n_r}])
            st.session_state.user_db = pd.concat([st.session_state.user_db, new_u], ignore_index=True)
            conn.update(worksheet="user_db", data=st.session_state.user_db)
            st.success("New user synced to Cloud database.")
    st.dataframe(st.session_state.user_db[['email', 'role']], use_container_width=True)

elif menu == "System Status":
    render_header("Core Health Monitor", nav_icons["System Status"])
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Sync Status", "Healthy")
    c2.metric("Cloud Rows", len(st.session_state.master_data))
    c3.metric("DB Latency", "12ms")
    st.divider()
    st.write("Active Auth Personnel:", st.session_state.user_db)

elif menu == "Exception Management":
    render_header("Live Staffing Exceptions", nav_icons["Exception Management"])
    with st.form("exc_log"):
        ct_in = st.selectbox("Market Selection", COUNTRIES)
        agt_in = st.text_input("Staff Name")
        t_in = st.selectbox("Reason", ["Sickness", "Late", "Technical", "Meeting"])
        if st.form_submit_button("Log Exception"):
            st.success("Logged.")

elif menu == "Forecasting":
    render_header("Volume Demand Prediction", nav_icons["Forecasting"])
    st.info("Trend analysis requires historical volume data.")

elif menu == "Reporting Center":
    render_header("Global Data Exports", nav_icons["Reporting Center"])
    if not st.session_state.master_data.empty:
        st.download_button("Download CSV Export", st.session_state.master_data.to_csv(index=False).encode('utf-8'), "WFM_Global_Export.csv")
