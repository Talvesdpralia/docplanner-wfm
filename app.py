import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio
from datetime import datetime
import math
from streamlit_gsheets import GSheetsConnection

# 1. UI & DESIGN ENGINE
st.set_page_config(page_title="Docplanner WFM", layout="wide", page_icon="🏥")

DP_TEAL = "#00c4a7"
DP_NAVY = "#011e41"
DP_SLATE = "#4b5563"

def apply_custom_design():
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Figtree:wght@300;400;500;600&display=swap');
        
        /* Global Font & Stage Compactness */
        html, body, [class*="css"] {{
            font-family: 'Figtree', sans-serif !important;
            font-size: 13px !important; 
        }}

        /* HIDE RADIO CIRCLES */
        [data-testid="stSidebar"] [data-testid="stWidgetLabel"] {{ display: none; }}
        [data-testid="stSidebar"] div[role="radiogroup"] label div:first-child {{
            display: none !important;
        }}
        
        /* Navigation Menu Items */
        [data-testid="stSidebar"] div[role="radiogroup"] label {{
            padding: 6px 12px !important;
            margin: 1px 0px !important;
            border-radius: 10px !important;
            transition: all 0.2s ease;
        }}
        [data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
            background: rgba(0, 196, 167, 0.04) !important;
        }}
        [data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] {{
            background: rgba(0, 196, 167, 0.08) !important;
            color: {DP_TEAL} !important;
        }}

        /* REALISTIC SHADOW INPUTS (AI Prompt Style) */
        .stTextInput input, .stSelectbox div[data-baseweb="select"], .stNumberInput input {{
            background-color: rgba(255, 255, 255, 0.8) !important;
            backdrop-filter: blur(8px);
            border: 1px solid rgba(0, 0, 0, 0.03) !important;
            border-radius: 20px !important; 
            padding: 6px 14px !important;
            /* Multi-layered soft shadow for realism */
            box-shadow: 0 2px 4px rgba(0,0,0,0.02), 0 10px 20px rgba(0,0,0,0.04) !important;
            transition: box-shadow 0.3s ease, border 0.3s ease;
        }}
        .stTextInput input:focus {{
            border: 1px solid {DP_TEAL} !important;
            box-shadow: 0 0 0 2px rgba(0, 196, 167, 0.1) !important;
        }}

        /* Header Overhaul */
        h1 {{ font-weight: 300 !important; font-size: 1.4rem !important; color: {DP_NAVY}; letter-spacing: -0.4px; }}
        h2 {{ font-weight: 400 !important; font-size: 1.0rem !important; color: {DP_SLATE}; }}

        /* Sidebar Glass */
        section[data-testid="stSidebar"] {{
            background: rgba(255, 255, 255, 0.01) !important;
            backdrop-filter: blur(35px);
            border-right: 1px solid rgba(0, 0, 0, 0.04);
        }}

        /* Metric Cards */
        [data-testid="stMetric"] {{
            background: #ffffff;
            border: 1px solid rgba(0, 0, 0, 0.02);
            padding: 15px !important;
            border-radius: 14px !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        }}

        /* Section Icon Style */
        .header-container {{ display: flex; align-items: center; gap: 8px; margin-bottom: 20px; }}
        .header-icon {{ font-size: 1.2rem; color: {DP_TEAL}; opacity: 0.7; }}
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
        st.image(DP_LOGO, width=170)
        st.title("WFM Workspace")
        e_in = st.text_input("Work Email", placeholder="email@docplanner.com")
        p_in = st.text_input("Password", type="password", placeholder="••••••••")
        if st.button("Sign In", use_container_width=True):
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
# Fixed dictionary syntax
nav_icons = {
    "Dashboard": "⟢", "Import Data": "⤓", "Forecasting": "📈", 
    "Exception Management": "⚠", "Capacity Planner (Erlang)": "◈", 
    "Reporting Center": "▤", "Admin Panel": "⚙", "System Status": "🛡"
}

available_nav = ["Dashboard", "Forecasting"]
if role == "Admin": available_nav.insert(1, "Import Data")
if role in ["Admin", "Manager"]: available_nav.extend(["Exception Management", "Capacity Planner (Erlang)"])
if role == "Admin": available_nav.extend(["Reporting Center", "Admin Panel", "System Status"])

with st.sidebar:
    st.image(DP_LOGO, width=130)
    st.write(f"**{st.session_state.current_email}**")
    st.divider()
    
    menu = st.radio("Nav", available_nav)
    
    st.divider()
    view_mode = st.radio("View", ["Global", "Regional Select"])
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

# 7. INTERFACE RENDERER
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
            c1.metric("Volume", f"{df_f['Volume'].sum():,.0f}")
            c2.metric("SL%", f"{(df_f['Volume']*df_f['SL']).sum()/df_f['Volume'].sum():.1f}%" if df_f['Volume'].sum() > 0 else "0%")
            c3.metric("AHT", f"{int(df_f['AHT'].mean())}s")
            c4.metric("FTE", f"{df_f['FTE'].sum():,.1f}")
            st.divider()
            st.plotly_chart(px.line(df_f, x='Date', y='Volume', color='Country', template="plotly_white"), use_container_width=True)
    else: st.info("Cloud database empty.")

elif menu == "Import Data":
    render_header("Data Ingestion", nav_icons["Import Data"])
    target = st.selectbox("Market", COUNTRIES)
    up = st.file_uploader("Drop CSV", type="csv")
    if up:
        new_df = pd.read_csv(up)
        new_df['Country'] = target
        st.session_state.master_data = pd.concat([st.session_state.master_data[st.session_state.master_data['Country'] != target], new_df], ignore_index=True)
        conn.update(worksheet="master_data", data=st.session_state.master_data)
        st.success("Synced.")

elif menu == "Capacity Planner (Erlang)":
    render_header("Staffing Engine", nav_icons["Capacity Planner (Erlang)"])
    
    col1, col2 = st.columns(2)
    with col1:
        v_h = st.number_input("Peak Volume", value=200)
        a_s = st.number_input("Target AHT", value=300)
    with col2:
        s_t = st.slider("SL Target %", 50, 99, 80) / 100
        sh = st.slider("Shrinkage %", 0, 50, 20) / 100
    if v_h > 0:
        req = math.ceil((v_h * a_s) / 3600) + 1
        ach = 0
        while ach < s_t and req < 500:
            ach = calculate_erlang_c(v_h, a_s, 20, req)
            if ach < s_t: req += 1
        st.metric("Required FTE", f"{math.ceil(req / (1 - sh))}")

elif menu == "Admin Panel":
    render_header("Access Control", nav_icons["Admin Panel"])
    with st.form("new_user"):
        n_e = st.text_input("Email")
        n_p = st.text_input("Password")
        n_r = st.selectbox("Role", ["Admin", "Manager", "User"])
        if st.form_submit_button("Provision"):
            new_u = pd.DataFrame([{"email": n_e, "password": n_p, "role": n_r}])
            st.session_state.user_db = pd.concat([st.session_state.user_db, new_u], ignore_index=True)
            conn.update(worksheet="user_db", data=st.session_state.user_db)
            st.success("Account created.")
    st.dataframe(st.session_state.user_db[['email', 'role']], use_container_width=True)
