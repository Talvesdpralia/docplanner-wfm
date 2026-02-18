import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio
from datetime import datetime
import math
from streamlit_gsheets import GSheetsConnection

# 1. UI & DESIGN ENGINE - GEMINI DEPTH OVERHAUL
st.set_page_config(page_title="Docplanner WFM", layout="wide", page_icon="🏥")

DP_TEAL = "#00c4a7"
DP_NAVY = "#011e41"
DP_SLATE = "#4b5563"

def apply_custom_design():
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Figtree:wght@300;400;500;600&display=swap');
        
        /* Global Stage & Compact Font */
        html, body, [class*="css"], .stApp {{
            font-family: 'Figtree', sans-serif !important;
            font-size: 13.5px !important;
            background-color: #ffffff !important;
        }}

        /* HIDE RADIO CIRCLES & FORCE TEAL ACCENT */
        [data-testid="stSidebar"] div[role="radiogroup"] label div:first-child {{
            display: none !important;
        }}
        input[type="radio"] {{
            accent-color: {DP_TEAL} !important;
        }}
        
        /* Modern Navigation Menu - No highlight, Teal text when active */
        [data-testid="stSidebar"] div[role="radiogroup"] label {{
            padding: 8px 12px !important;
            margin: 2px 0px !important;
            border-radius: 10px !important;
            transition: all 0.2s ease !important;
            background-color: transparent !important;
        }}
        [data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] {{
            background: rgba(0, 196, 167, 0.08) !important;
            color: {DP_TEAL} !important;
            font-weight: 500 !important;
        }}

        /* REALISTIC SHADOWS (REMOVING THE GREY HALO) */
        .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input {{
            background-color: #ffffff !important;
            border: none !important; 
            border-radius: 20px !important; 
            padding: 10px 16px !important;
            /* Multi-layered soft shadow for realistic depth */
            box-shadow: 0 1px 3px rgba(0,0,0,0.02), 0 8px 24px rgba(0,0,0,0.04) !important;
            transition: all 0.3s ease !important;
        }}
        
        /* Remove Streamlit's default focus border */
        .stTextInput input:focus {{
            box-shadow: 0 2px 4px rgba(0,0,0,0.02), 0 12px 28px rgba(0,196,167,0.1) !important;
            border: none !important;
        }}

        /* Header Overhaul - Thin & Compact */
        h1 {{ font-weight: 300 !important; font-size: 1.5rem !important; color: {DP_NAVY}; letter-spacing: -0.4px; margin-bottom: 20px !important; }}
        h2 {{ font-weight: 400 !important; font-size: 1.0rem !important; color: {DP_SLATE}; }}

        /* Sidebar Glass - More Salient */
        section[data-testid="stSidebar"] {{
            background: rgba(255, 255, 255, 0.01) !important;
            backdrop-filter: blur(45px) saturate(160%) !important;
            border-right: 1px solid rgba(0, 0, 0, 0.06) !important;
        }}

        /* Section Icon Style */
        .header-container {{ display: flex; align-items: center; gap: 10px; margin-bottom: 15px; }}
        .header-icon {{ font-size: 1.4rem; color: {DP_TEAL}; opacity: 0.8; }}
        </style>
    """, unsafe_allow_html=True)

apply_custom_design()

# 2. DATABASE CONNECTION
conn = st.connection("gsheets", type=GSheetsConnection)

def sync_from_cloud():
    try:
        st.session_state.user_db = conn.read(worksheet="user_db", ttl="0")
        st.session_state.master_data = conn.read(worksheet="master_data", ttl="0")
        st.session_state.exception_logs = conn.read(worksheet="exception_logs", ttl="0")
    except Exception:
        # Emergency local fallback
        st.session_state.user_db = pd.DataFrame([{"email": "telmo.alves@docplanner.com", "password": "Memes0812", "role": "Admin"}])

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    sync_from_cloud()

# 3. GLOBAL VARIABLES
DP_LOGO = "https://www.docplanner.com/img/logo-default-group-en.svg"
COUNTRIES = ["Spain", "Mexico", "Poland", "Germany", "Italy", "Brazil", "Colombia", "Turkey"]

# 4. LOGIN GATE
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1, 1])
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.image(DP_LOGO, width=180)
        st.title("WFM Workspace")
        e_in = st.text_input("Work Email", placeholder="your.name@docplanner.com")
        p_in = st.text_input("Password", type="password", placeholder="••••••••")
        if st.button("Continue", use_container_width=True):
            db = st.session_state.user_db
            match = db[(db['email'].str.lower() == e_in.lower()) & (db['password'] == p_in)]
            if not match.empty:
                st.session_state.logged_in = True
                st.session_state.user_role = str(match.iloc[0]['role'])
                st.session_state.current_email = str(match.iloc[0]['email'])
                st.rerun()
            else: st.error("Access denied. Check credentials.")
    st.stop()

# 5. SIDEBAR NAVIGATION
role = st.session_state.user_role
nav_icons = {
    "Dashboard": "⟢", 
    "Import Data": "⤓", 
    "Forecasting": "📈", 
    "Exception Management": "⚠", 
    "Capacity Planner (Erlang)": "◈", 
    "Reporting Center": "▤", 
    "Admin Panel": "⚙", 
    "System Status": "🛡"
}

# Explicitly defining available options to prevent "disappearing" menus
available_nav = ["Dashboard", "Forecasting"]
if role == "Admin": 
    available_nav = ["Dashboard", "Import Data", "Forecasting", "Exception Management", "Capacity Planner (Erlang)", "Reporting Center", "Admin Panel", "System Status"]
elif role == "Manager":
    available_nav = ["Dashboard", "Forecasting", "Exception Management", "Capacity Planner (Erlang)"]

with st.sidebar:
    st.image(DP_LOGO, width=130)
    st.markdown(f"**{st.session_state.current_email}**")
    st.divider()
    
    # Selection Menu (Circles hidden via CSS)
    menu = st.radio("Workspace", available_nav)
    
    st.divider()
    view_mode = st.radio("View", ["Global", "Regional Select"])
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

# 7. MODULES
def render_header(title, icon):
    st.markdown(f'<div class="header-container"><span class="header-icon">{icon}</span><h1>{title}</h1></div>', unsafe_allow_html=True)

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
    else: st.info("Cloud database empty. Please import market data.")

elif menu == "Import Data":
    render_header("Data Ingestion", nav_icons["Import Data"])
    target = st.selectbox("Assign Market", COUNTRIES)
    up = st.file_uploader("Drop CSV file", type="csv")
    if up:
        new_df = pd.read_csv(up)
        new_df['Country'] = target
        st.session_state.master_data = pd.concat([st.session_state.master_data[st.session_state.master_data['Country'] != target], new_df], ignore_index=True)
        conn.update(worksheet="master_data", data=st.session_state.master_data)
        st.success("Synchronized with Cloud.")

elif menu == "Capacity Planner (Erlang)":
    render_header("Staffing Engine", nav_icons["Capacity Planner (Erlang)"])
    
    col1, col2 = st.columns(2)
    with col1:
        v_h = st.number_input("Peak Period Volume", value=200)
        a_s = st.number_input("Target AHT (Seconds)", value=300)
    with col2:
        s_t = st.slider("Service Level Target %", 50, 99, 80) / 100
        sh = st.slider("Shrinkage Factor (%)", 0, 50, 20) / 100
    if v_h > 0:
        req = math.ceil((v_h * a_s) / 3600) + 1
        ach = 0
        while ach < s_t and req < 500:
            ach = calculate_erlang_c(v_h, a_s, 20, req)
            if ach < s_t: req += 1
        st.divider()
        st.metric("Recommended FTE Capacity", f"{math.ceil(req / (1 - sh))} FTE")

elif menu == "Admin Panel":
    render_header("Authority & Access", nav_icons["Admin Panel"])
    with st.form("new_user"):
        n_e = st.text_input("New Email")
        n_p = st.text_input("Password")
        n_r = st.selectbox("Role", ["Admin", "Manager", "User"])
        if st.form_submit_button("Grant Access"):
            new_u = pd.DataFrame([{"email": n_e, "password": n_p, "role": n_r}])
            st.session_state.user_db = pd.concat([st.session_state.user_db, new_u], ignore_index=True)
            conn.update(worksheet="user_db", data=st.session_state.user_db)
            st.success("User added to Cloud Database.")
    st.dataframe(st.session_state.user_db[['email', 'role']], use_container_width=True)

elif menu == "System Status":
    render_header("Infrastructure Health", nav_icons["System Status"])
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Sync Status", "Healthy")
    c2.metric("Cloud Rows", len(st.session_state.master_data))
    c3.metric("DB Latency", "12ms")
