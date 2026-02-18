import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio
from datetime import datetime
import math
from streamlit_gsheets import GSheetsConnection

# 1. DESIGN ENGINE - THE ULTIMATE UI CLEANUP
st.set_page_config(page_title="Docplanner WFM Pro", layout="wide", page_icon="🏥")

DP_TEAL = "#00c4a7"
DP_NAVY = "#011e41"
DP_SLATE = "#4b5563"

def apply_custom_design():
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Figtree:wght@300;400;500;600&display=swap');
        
        /* Global Stage - Mesh Background */
        html, body, [class*="css"], .stApp {{
            font-family: 'Figtree', sans-serif !important;
            font-size: 14px !important;
            background: radial-gradient(at 0% 0%, rgba(0, 196, 167, 0.03) 0px, transparent 50%),
                        radial-gradient(at 100% 100%, rgba(1, 30, 65, 0.02) 0px, transparent 50%),
                        #ffffff !important;
        }}

        /* KILL ALL DEFAULT GREY BORDERS & RED ACCENTS */
        :root {{
            --primary-color: {DP_TEAL} !important;
        }}
        
        /* Remove the red circle from ALL radio buttons (Navigation + View) */
        div[data-testid="stMarkdownContainer"] p {{
            font-weight: 300;
        }}
        
        /* Force Teal Accent on all inputs */
        input[type="radio"] {{
            accent-color: {DP_TEAL} !important;
        }}

        /* HIDE NAVIGATION RADIO CIRCLES COMPLETELY */
        [data-testid="stSidebar"] div[role="radiogroup"] label div:first-child {{
            display: none !important;
        }}

        /* SIDEBAR - DEEP GLASS & CLEAN NAV */
        section[data-testid="stSidebar"] {{
            background: rgba(255, 255, 255, 0.02) !important;
            backdrop-filter: blur(50px) saturate(190%) !important;
            border-right: 1px solid rgba(0, 0, 0, 0.05) !important;
        }}

        [data-testid="stSidebar"] div[role="radiogroup"] label {{
            padding: 12px 16px !important;
            margin: 6px 0px !important;
            border-radius: 12px !important;
            transition: all 0.3s ease !important;
            font-weight: 300 !important;
            color: {DP_NAVY} !important;
        }}

        [data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] {{
            background: rgba(0, 196, 167, 0.08) !important;
            color: {DP_TEAL} !important;
            font-weight: 500 !important;
        }}

        /* CLEAN PROMPT BOXES - REMOVING ALL GREY HALOS */
        /* Targets Text, Number, and Dropdown (Selectbox) inputs */
        .stTextInput input, .stSelectbox div[data-baseweb="select"], 
        .stNumberInput input, .stMultiSelect div[data-baseweb="select"] {{
            background-color: #ffffff !important;
            border: none !important; 
            outline: none !important;
            border-radius: 24px !important; 
            padding: 10px 18px !important;
            box-shadow: 0 2px 4px rgba(0,0,0,0.01), 0 8px 16px rgba(0,0,0,0.04) !important;
            transition: all 0.3s ease !important;
        }}
        
        /* Target the wrapper that often causes the 'grey halo' */
        div[data-baseweb="input"], div[data-baseweb="select"] {{
            border: none !important;
            background: transparent !important;
            box-shadow: none !important;
        }}

        .stTextInput input:focus, .stSelectbox div[data-baseweb="select"]:focus {{
            box-shadow: 0 10px 30px rgba(0, 196, 167, 0.12) !important;
            transform: translateY(-1px);
        }}

        /* Metrics Glass Style */
        [data-testid="stMetric"] {{
            background: rgba(255, 255, 255, 0.7) !important;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(0, 196, 167, 0.1) !important;
            padding: 20px !important;
            border-radius: 20px !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.03) !important;
        }}

        /* Titles - Thin & Modern */
        h1 {{ font-weight: 300 !important; font-size: 1.8rem !important; color: {DP_NAVY}; }}
        h2 {{ font-weight: 400 !important; font-size: 1.1rem !important; color: {DP_SLATE}; }}

        /* Button Styling */
        .stButton>button {{
            background: {DP_TEAL} !important;
            color: white !important;
            border-radius: 24px !important;
            border: none !important;
            padding: 10px 30px !important;
            font-weight: 500 !important;
            box-shadow: 0 6px 15px rgba(0, 196, 167, 0.25) !important;
        }}
        </style>
    """, unsafe_allow_html=True)

apply_custom_design()

# 2. DATABASE CONNECTION (GOOGLE SHEETS)
conn = st.connection("gsheets", type=GSheetsConnection)

def sync_from_cloud():
    try:
        st.session_state.user_db = conn.read(worksheet="user_db", ttl="0")
        st.session_state.master_data = conn.read(worksheet="master_data", ttl="0")
        st.session_state.exception_logs = conn.read(worksheet="exception_logs", ttl="0")
    except:
        # Fallback super admin account
        st.session_state.user_db = pd.DataFrame([{"email": "telmo.alves@docplanner.com", "password": "Memes0812", "role": "Admin"}])

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    sync_from_cloud()

# 3. GLOBAL ASSETS
DP_LOGO = "https://www.docplanner.com/img/logo-default-group-en.svg"
COUNTRIES = ["Spain", "Mexico", "Poland", "Germany", "Italy", "Brazil", "Colombia", "Turkey"]

# 4. LOGIN GATE
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.image(DP_LOGO, width=200)
        st.title("Workforce Hub")
        e_in = st.text_input("Email", placeholder="telmo.alves@docplanner.com")
        p_in = st.text_input("Password", type="password", placeholder="••••••••")
        if st.button("Continue", use_container_width=True):
            db = st.session_state.user_db
            match = db[(db['email'].str.lower() == e_in.lower()) & (db['password'] == p_in)]
            if not match.empty:
                st.session_state.logged_in = True
                st.session_state.user_role = str(match.iloc[0]['role'])
                st.session_state.current_email = str(match.iloc[0]['email'])
                st.rerun()
            else: st.error("Authentication failed.")
    st.stop()

# 5. SIDEBAR NAVIGATION - ALL OPTIONS SHOWING
role = st.session_state.user_role
nav_icons = {
    "Dashboard": "⟢", "Import Data": "⤓", "Forecasting": "📈", 
    "Exception Management": "⚠", "Capacity Planner (Erlang)": "◈", 
    "Reporting Center": "▤", "Admin Panel": "⚙", "System Status": "🛡"
}

# Full Admin Menu
if role == "Admin":
    menu_options = ["Dashboard", "Import Data", "Forecasting", "Exception Management", "Capacity Planner (Erlang)", "Reporting Center", "Admin Panel", "System Status"]
else:
    menu_options = ["Dashboard", "Forecasting", "Exception Management", "Capacity Planner (Erlang)"]

with st.sidebar:
    st.image(DP_LOGO, width=150)
    st.markdown(f"**{st.session_state.current_email}**")
    st.divider()
    
    # Navigation Radio - All options visible, circles hidden
    menu = st.radio("Navigation Menu", menu_options)
    
    st.divider()
    # View Setting Radio - Accented teal circle
    view_mode = st.radio("View Setting", ["Global", "Regional Select"])
    selected_markets = COUNTRIES
    if view_mode == "Regional Select":
        selected_markets = st.multiselect("Markets", COUNTRIES, default=COUNTRIES)
    
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

# 7. MAIN INTERFACE MODULES
def render_header(title, icon):
    st.markdown(f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:30px;"><span style="font-size:1.6rem;color:{DP_TEAL};opacity:0.8;">{icon}</span><h1>{title}</h1></div>', unsafe_allow_html=True)

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
    target = st.selectbox("Assign Market", COUNTRIES)
    up = st.file_uploader("Drop Market CSV", type="csv")
    if up:
        new_df = pd.read_csv(up)
        new_df['Country'] = target
        st.session_state.master_data = pd.concat([st.session_state.master_data[st.session_state.master_data['Country'] != target], new_df], ignore_index=True)
        conn.update(worksheet="master_data", data=st.session_state.master_data)
        st.success("Synced to Google Sheets.")

elif menu == "Admin Panel":
    render_header("Authority & Access", nav_icons["Admin Panel"])
    with st.form("user_add"):
        n_e = st.text_input("New User Email")
        n_p = st.text_input("Password")
        n_r = st.selectbox("Role", ["Admin", "Manager", "User"])
        if st.form_submit_button("Grant Access"):
            new_u = pd.DataFrame([{"email": n_e, "password": n_p, "role": n_r}])
            st.session_state.user_db = pd.concat([st.session_state.user_db, new_u], ignore_index=True)
            conn.update(worksheet="user_db", data=st.session_state.user_db)
            st.success("User added.")
    st.dataframe(st.session_state.user_db[['email', 'role']], use_container_width=True)

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
        st.metric("Recommended FTE Capacity", f"{math.ceil(req / (1 - sh))} FTE")
