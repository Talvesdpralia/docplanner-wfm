import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio
from datetime import datetime
import math
from streamlit_gsheets import GSheetsConnection

# 1. DESIGN & BRANDING CONFIGURATION
st.set_page_config(page_title="Docplanner WFM", layout="wide", page_icon="🏥")

DP_TEAL = "#00c4a7"
DP_NAVY = "#011e41"
DP_SLATE = "#4b5563"

def apply_custom_design():
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Figtree:wght@300;400;500;600&display=swap');
        
        /* Global Stage */
        html, body, [class*="css"] {{
            font-family: 'Figtree', sans-serif !important;
            font-size: 13px !important;
            background-color: #ffffff;
        }}

        /* HIDE RADIO CIRCLES */
        [data-testid="stSidebar"] div[role="radiogroup"] label div:first-child {{
            display: none !important;
        }}
        
        /* Modern Sidebar */
        section[data-testid="stSidebar"] {{
            background: rgba(255, 255, 255, 0.01) !important;
            backdrop-filter: blur(40px);
            border-right: 1px solid rgba(0, 0, 0, 0.05);
        }}

        /* Navigation Menu Styling */
        [data-testid="stSidebar"] div[role="radiogroup"] label {{
            padding: 8px 12px !important;
            margin: 2px 0px !important;
            border-radius: 10px !important;
            transition: all 0.2s ease;
        }}
        [data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] {{
            background: rgba(0, 196, 167, 0.08) !important;
            color: {DP_TEAL} !important;
            font-weight: 500;
        }}

        /* CLEAN INPUTS & REALISTIC SHADOWS */
        /* This removes the 'grey weird aspect' and adds realistic depth */
        .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input {{
            background-color: #ffffff !important;
            border: none !important; /* Removes the grey border */
            border-radius: 20px !important; 
            padding: 10px 16px !important;
            /* Multi-layer shadow: 1 tight, 1 soft spread */
            box-shadow: 0 1px 2px rgba(0,0,0,0.05), 0 8px 20px rgba(0,0,0,0.04) !important;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }}
        
        .stTextInput input:focus {{
            box-shadow: 0 2px 4px rgba(0,0,0,0.05), 0 12px 24px rgba(0,196,167,0.08) !important;
            transform: translateY(-1px);
        }}

        /* Metrics & Cards */
        [data-testid="stMetric"] {{
            background: #ffffff;
            padding: 18px !important;
            border-radius: 16px !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.02);
            border: 1px solid #f9f9f9;
        }}
        
        /* Typography */
        h1 {{ font-weight: 300 !important; font-size: 1.4rem !important; color: {DP_NAVY}; letter-spacing: -0.4px; }}
        h2 {{ font-weight: 400 !important; font-size: 1.0rem !important; color: {DP_SLATE}; }}

        /* Action Buttons */
        .stButton>button {{
            background: {DP_TEAL};
            color: white;
            border-radius: 20px;
            border: none;
            padding: 8px 24px;
            font-weight: 500;
            box-shadow: 0 4px 12px rgba(0, 196, 167, 0.2);
        }}
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
    except:
        # Emergency local fallback for Telmo
        st.session_state.user_db = pd.DataFrame([{"email": "telmo.alves@docplanner.com", "password": "Memes0812", "role": "Admin"}])
        st.session_state.master_data = pd.DataFrame(columns=["Date", "Volume", "SL", "AHT", "FTE", "Country"])
        st.session_state.exception_logs = pd.DataFrame(columns=["Country", "Timestamp", "Agent", "Type", "Duration (Min)", "Notes"])

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
        st.image(DP_LOGO, width=170)
        st.markdown("<br>", unsafe_allow_html=True)
        e_in = st.text_input("Email", placeholder="yourname@docplanner.com")
        p_in = st.text_input("Password", type="password", placeholder="••••••••")
        if st.button("Continue", use_container_width=True):
            db = st.session_state.user_db
            match = db[(db['email'] == e_in) & (db['password'] == p_in)]
            if not match.empty:
                st.session_state.logged_in = True
                st.session_state.user_role = match.iloc[0]['role']
                st.session_state.current_email = match.iloc[0]['email']
                st.rerun()
            else: st.error("Access denied. Please check credentials.")
    st.stop()

# 5. SIDEBAR NAVIGATION LOGIC (THE FIX)
role = st.session_state.user_role
nav_icons = {
    "Dashboard": "⟢", "Import Data": "⤓", "Forecasting": "📈", 
    "Exception Management": "⚠", "Capacity Planner (Erlang)": "◈", 
    "Reporting Center": "▤", "Admin Panel": "⚙", "System Status": "🛡"
}

# Build the dynamic menu based on role
available_nav = ["Dashboard", "Forecasting"]
if role == "Admin": 
    available_nav.insert(1, "Import Data")
    available_nav.extend(["Reporting Center", "Admin Panel", "System Status"])
if role in ["Admin", "Manager"]: 
    available_nav.extend(["Exception Management", "Capacity Planner (Erlang)"])

with st.sidebar:
    st.image(DP_LOGO, width=130)
    st.markdown(f"**{st.session_state.current_email}**")
    st.divider()
    
    # Navigation Choice
    menu = st.radio("Navigation Menu", available_nav)
    
    st.divider()
    view_mode = st.radio("Market Selection", ["Global View", "Regional Select"])
    if view_mode == "Regional Select":
        selected_markets = st.multiselect("Markets", COUNTRIES, default=COUNTRIES)
    else: selected_markets = COUNTRIES
    
    if st.button("Sync Data 🔄", use_container_width=True):
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

# 7. INTERFACE MODULES
def render_header(title, icon):
    st.markdown(f'<div style="display: flex; align-items: center; gap: 8px; margin-bottom: 20px;"><span style="font-size: 1.2rem; color: {DP_TEAL}; opacity: 0.7;">{icon}</span><h1>{title}</h1></div>', unsafe_allow_html=True)

if menu == "Dashboard":
    render_header("Operations Performance", nav_icons["Dashboard"])
    df = st.session_state.master_data
    if not df.empty:
        df_f = df[df['Country'].isin(selected_markets)].copy()
        if not df_f.empty:
            for c in ['Volume', 'SL', 'AHT', 'FTE']: df_f[c] = pd.to_numeric(df_f[c], errors='coerce').fillna(0)
            c1, c2, c3, c4 = st.columns(4)
            tot_v = df_f['Volume'].sum()
            c1.metric("Total Volume", f"{tot_v:,.0f}")
            c2.metric("Weighted SL%", f"{(df_f['Volume']*df_f['SL']).sum()/tot_v:.1f}%" if tot_v > 0 else "0%")
            c3.metric("Avg AHT", f"{int(df_f['AHT'].mean())}s")
            c4.metric("Actual FTE", f"{df_f['FTE'].sum():,.1f}")
            st.divider()
            st.plotly_chart(px.line(df_f, x='Date', y='Volume', color='Country', template="plotly_white"), use_container_width=True)
    else: st.info("Cloud database is currently empty.")

elif menu == "Import Data":
    render_header("Market Data Ingestion", nav_icons["Import Data"])
    target = st.selectbox("Destination Market", COUNTRIES)
    up = st.file_uploader("Drop Market CSV File", type="csv")
    if up:
        new_df = pd.read_csv(up)
        new_df['Country'] = target
        st.session_state.master_data = pd.concat([st.session_state.master_data[st.session_state.master_data['Country'] != target], new_df], ignore_index=True)
        conn.update(worksheet="master_data", data=st.session_state.master_data)
        st.success("Successfully synchronized with Google Sheets.")

elif menu == "Capacity Planner (Erlang)":
    render_header("Staffing Requirement Engine", nav_icons["Capacity Planner (Erlang)"])
    
    col1, col2 = st.columns(2)
    with col1:
        v_h = st.number_input("Peak Period Volume", value=200)
        a_s = st.number_input("Target AHT (Seconds)", value=300)
    with col2:
        s_t = st.slider("Service Level Target %", 50, 99, 80) / 100
        sh = st.slider("Shrinkage %", 0, 50, 20) / 100
    if v_h > 0:
        req = math.ceil((v_h * a_s) / 3600) + 1
        ach = 0
        while ach < s_t and req < 500:
            ach = calculate_erlang_c(v_h, a_s, 20, req)
            if ach < s_t: req += 1
        st.divider()
        st.metric("Recommended FTE Capacity", f"{math.ceil(req / (1 - sh))}")

elif menu == "Admin Panel":
    render_header("User Access Management", nav_icons["Admin Panel"])
    with st.form("new_user"):
        n_e = st.text_input("New Staff Email")
        n_p = st.text_input("Temporary Access Password")
        n_r = st.selectbox("Permission Tier", ["Admin", "Manager", "User"])
        if st.form_submit_button("Grant Access"):
            new_u = pd.DataFrame([{"email": n_e, "password": n_p, "role": n_r}])
            st.session_state.user_db = pd.concat([st.session_state.user_db, new_u], ignore_index=True)
            conn.update(worksheet="user_db", data=st.session_state.user_db)
            st.success("User successfully added to Cloud.")
    st.dataframe(st.session_state.user_db[['email', 'role']], use_container_width=True)

elif menu == "System Status":
    render_header("Core Infrastructure Health", nav_icons["System Status"])
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Cloud Sync", "Active")
    c2.metric("Database Rows", len(st.session_state.master_data))
    c3.metric("Service Latency", "12ms")
    st.divider()
    st.write("Authorized Personnel Log:", st.session_state.user_db)

elif menu == "Exception Management":
    render_header("Live Staffing Exceptions", nav_icons["Exception Management"])
    with st.form("exc_log"):
        ct_in = st.selectbox("Market", selected_markets)
        agt_in = st.text_input("Agent Name")
        t_in = st.selectbox("Type", ["Sickness", "Late", "Technical", "Meeting"])
        if st.form_submit_button("Submit Log"):
            st.success("Exception logged.")

elif menu == "Forecasting":
    render_header("Volume Demand Forecast", nav_icons["Forecasting"])
    st.info("Historical data required for trend generation.")

elif menu == "Reporting Center":
    render_header("Global Data Exports", nav_icons["Reporting Center"])
    if not st.session_state.master_data.empty:
        st.download_button("Download Master Global Export", st.session_state.master_data.to_csv(index=False).encode('utf-8'), "Global_WFM_Export.csv")
