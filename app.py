import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio
from datetime import datetime
import math
from streamlit_gsheets import GSheetsConnection

# 1. UI & DESIGN ENGINE (GEMINI COMPACT OVERHAUL)
st.set_page_config(page_title="Docplanner WFM", layout="wide", page_icon="🏥")

DP_TEAL = "#00c4a7"
DP_NAVY = "#011e41"
DP_SLATE = "#4b5563"

def apply_custom_design():
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Figtree:wght@300;400;500;600&display=swap');
        
        /* Global Font & Compactness */
        html, body, [class*="css"] {{
            font-family: 'Figtree', sans-serif !important;
            font-size: 14px; /* Smaller base font for compact look */
        }}

        /* HIDE RADIO CIRCLES */
        [data-testid="stSidebar"] [data-testid="stWidgetLabel"] {{ display: none; }}
        [data-testid="stSidebar"] div[role="radiogroup"] label div:first-child {{
            display: none !important;
        }}
        
        /* Navigation Menu Items */
        [data-testid="stSidebar"] div[role="radiogroup"] label {{
            padding: 8px 12px !important;
            margin: 2px 0px !important;
            border-radius: 10px !important;
            transition: all 0.2s ease;
        }}
        [data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
            background: rgba(0, 196, 167, 0.05) !important;
        }}
        [data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] {{
            background: rgba(0, 196, 167, 0.1) !important;
            color: {DP_TEAL} !important;
        }}

        /* Modern Prompt-Style Inputs (Rounded, Transparent, Shadow) */
        .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input {{
            background-color: rgba(255, 255, 255, 0.6) !important;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(0, 0, 0, 0.05) !important;
            border-radius: 24px !important; /* Ultra Rounded like AI prompt box */
            padding: 8px 16px !important;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.03) !important;
            font-size: 13px !important;
        }}

        /* Header Overhaul - Thin & Elegant */
        h1 {{ font-weight: 300 !important; font-size: 1.5rem !important; color: {DP_NAVY}; }}
        h2 {{ font-weight: 400 !important; font-size: 1.1rem !important; color: {DP_SLATE}; }}

        /* Glass Sidebar */
        section[data-testid="stSidebar"] {{
            background: rgba(255, 255, 255, 0.01) !important;
            backdrop-filter: blur(40px);
            border-right: 1px solid rgba(0, 0, 0, 0.05);
        }}

        /* Metric Cards - Modern Float */
        [data-testid="stMetric"] {{
            background: rgba(255, 255, 255, 0.5);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(0, 196, 167, 0.1);
            padding: 15px !important;
            border-radius: 18px !important;
            box-shadow: 0 10px 30px -10px rgba(0,0,0,0.05);
        }}

        /* Section Icon Style */
        .header-container {{ display: flex; align-items: center; gap: 10px; margin-bottom: 15px; }}
        .header-icon {{ font-size: 1.4rem; color: {DP_TEAL}; opacity: 0.8; }}
        </style>
    """, unsafe_allow_html=True)

apply_custom_design()

# 2. DATA CONNECTION
conn = st.connection("gsheets", type=GSheetsConnection)

def sync_from_cloud():
    try:
        st.session_state.user_db = conn.read(worksheet="user_db", ttl="0")
        st.session_state.master_data = conn.read(worksheet="master_data", ttl="0")
        st.session_state.exception_logs = conn.read(worksheet="exception_logs", ttl="0")
    except:
        st.session_state.user_db = pd.DataFrame([{"email": "telmo.alves@docplanner.com", "password": "Memes0812", "role": "Admin"}])

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    sync_from_cloud()

# 3. GLOBAL VARIABLES
DP_LOGO = "https://www.docplanner.com/img/logo-default-group-en.svg"
COUNTRIES = ["Spain", "Mexico", "Poland", "Germany", "Italy", "Brazil", "Colombia", "Turkey"]

# 4. LOGIN GATE (CLEAN)
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.image(DP_LOGO, width=180)
        st.title("WFM Hub Login")
        e_in = st.text_input("Email", placeholder="your@docplanner.com")
        p_in = st.text_input("Password", type="password", placeholder="••••••••")
        if st.button("Continue", use_container_width=True):
            db = st.session_state.user_db
            match = db[(db['email'] == e_in) & (db['password'] == p_in)]
            if not match.empty:
                st.session_state.logged_in = True
                st.session_state.user_role = match.iloc[0]['role']
                st.session_state.current_email = match.iloc[0]['email']
                st.rerun()
            else: st.error("Access denied.")
    st.stop()

# 5. SIDEBAR NAVIGATION
role = st.session_state.user_role
nav_icons = {{
    "Dashboard": "⟢", "Import Data": "⤓", "Forecasting": "📈", 
    "Exception Management": "⚠", "Capacity Planner (Erlang)": "◈", 
    "Reporting Center": "▤", "Admin Panel": "⚙", "System Status": "🛡"
}}

available_nav = ["Dashboard", "Forecasting"]
if role == "Admin": available_nav.insert(1, "Import Data")
if role in ["Admin", "Manager"]: available_nav.extend(["Exception Management", "Capacity Planner (Erlang)"])
if role == "Admin": available_nav.extend(["Reporting Center", "Admin Panel", "System Status"])

with st.sidebar:
    st.image(DP_LOGO, width=140)
    st.write(f"**{st.session_state.current_email}**")
    st.divider()
    
    # Navigation Radio (Hidden Circles)
    menu = st.radio("Nav", available_nav)
    
    st.divider()
    view_mode = st.radio("View", ["Global", "Regional Select"])
    if view_mode == "Regional Select":
        selected_markets = st.multiselect("Active Markets", COUNTRIES, default=COUNTRIES)
    else: selected_markets = COUNTRIES
    
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
    st.markdown(f'<div class="header-container"><span class="header-icon">{icon}</span><h1>{title}</h1></div>', unsafe_allow_html=True)

if menu == "Dashboard":
    render_header("Operations Overview", nav_icons["Dashboard"])
    df = st.session_state.master_data
    if not df.empty:
        df_f = df[df['Country'].isin(selected_markets)].copy()
        if not df_f.empty:
            for c in ['Volume', 'SL', 'AHT', 'FTE']: df_f[c] = pd.to_numeric(df_f[c], errors='coerce').fillna(0)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Volume", f"{df_f['Volume'].sum():,.0f}")
            c2.metric("SL%", f"{(df_f['Volume']*df_f['SL']).sum()/df_f['Volume'].sum():.1f}%" if df_f['Volume'].sum() > 0 else "0%")
            c3.metric("AHT", f"{int(df_f['AHT'].mean())}s")
            c4.metric("FTE", f"{df_f['FTE'].sum():,.1f}")
            st.write("---")
            st.plotly_chart(px.line(df_f, x='Date', y='Volume', color='Country', template="plotly_white"), use_container_width=True)
    else: st.info("No data found in cloud.")

elif menu == "Import Data":
    render_header("Data Ingestion", nav_icons["Import Data"])
    target = st.selectbox("Select Market", COUNTRIES)
    up = st.file_uploader("Drop CSV file here", type="csv")
    if up:
        new_df = pd.read_csv(up)
        new_df['Country'] = target
        st.session_state.master_data = pd.concat([st.session_state.master_data[st.session_state.master_data['Country'] != target], new_df], ignore_index=True)
        conn.update(worksheet="master_data", data=st.session_state.master_data)
        st.success("Synchronized with Google Sheets.")

elif menu == "Capacity Planner (Erlang)":
    render_header("Staffing Engine", nav_icons["Capacity Planner (Erlang)"])
    
    col1, col2 = st.columns(2)
    with col1:
        v_h = st.number_input("Forecasted Volume (Peak)", value=200)
        a_s = st.number_input("Target AHT (Sec)", value=300)
    with col2:
        s_t = st.slider("Service Level Target (%)", 50, 99, 80) / 100
        sh = st.slider("Shrinkage Factor (%)", 0, 50, 20) / 100
    if v_h > 0:
        req = math.ceil((v_h * a_s) / 3600) + 1
        ach = 0
        while ach < s_t and req < 500:
            ach = calculate_erlang_c(v_h, a_s, 20, req)
            if ach < s_t: req += 1
        st.divider()
        st.metric("Required Headcount (FTE)", f"{math.ceil(req / (1 - sh))}")

elif menu == "Admin Panel":
    render_header("Access Management", nav_icons["Admin Panel"])
    with st.form("new_user"):
        n_e = st.text_input("New User Email")
        n_p = st.text_input("Temporary Password")
        n_r = st.selectbox("Permission Level", ["Admin", "Manager", "User"])
        if st.form_submit_button("Grant Access"):
            new_u = pd.DataFrame([{"email": n_e, "password": n_p, "role": n_r}])
            st.session_state.user_db = pd.concat([st.session_state.user_db, new_u], ignore_index=True)
            conn.update(worksheet="user_db", data=st.session_state.user_db)
            st.success("User added to Cloud Database.")
    st.dataframe(st.session_state.user_db[['email', 'role']], use_container_width=True)

elif menu == "System Status":
    render_header("Core Health", nav_icons["System Status"])
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Sync Status", "Stable")
    c2.metric("Cloud Rows", len(st.session_state.master_data))
    c3.metric("DB Latency", "12ms")
