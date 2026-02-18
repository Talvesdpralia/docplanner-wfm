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

def apply_custom_design():
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Figtree:wght@300;400;500;600&display=swap');
        
        /* Global Typography & Background */
        .stApp {{
            background: #FFFFFF;
            font-family: 'Figtree', sans-serif !important;
        }}

        /* Thinner, Smaller Headers (AI Style) */
        h1 {{
            font-weight: 300 !important;
            font-size: 1.6rem !important;
            letter-spacing: -0.5px;
            color: {DP_NAVY};
        }}
        h2, h3 {{
            font-weight: 300 !important;
            font-size: 1.1rem !important;
            color: #666;
        }}

        /* Sidebar & Navigation Fixes */
        section[data-testid="stSidebar"] {{
            background-color: #FBFBFB !important;
            border-right: 1px solid #F0F0F0;
        }}
        
        /* Force Teal Accent across the board */
        :root {{
            --primary-color: {DP_TEAL};
        }}
        
        /* Teal Pickers and Checkboxes */
        input[type="checkbox"], input[type="radio"] {{
            accent-color: {DP_TEAL} !important;
        }}

        /* Multiselect (Regional Select) Optimization */
        div[data-baseweb="select"] > div {{
            border-radius: 8px !important;
            border: 1px solid #EEE !important;
            min-height: 45px !important;
        }}
        /* Teal tags in multiselect */
        span[data-baseweb="tag"] {{
            background-color: {DP_TEAL} !important;
            border-radius: 6px !important;
        }}

        /* Navigation Menu - Thinner & Separated */
        div.row-widget.stRadio > div {{
            gap: 12px !important; /* Bigger space between options */
        }}
        div.row-widget.stRadio label {{
            font-weight: 300 !important; /* Thinner Font */
            font-size: 0.85rem !important;
            color: #555 !important;
            padding: 6px 10px !important;
        }}
        
        /* Active Navigation Item Teal Indicator */
        div[role="radiogroup"] label[data-baseweb="radio"] div:first-child {{
            border-color: {DP_TEAL} !important;
            background-color: {DP_TEAL} !important;
            transform: scale(0.8); /* Smaller Picker */
        }}

        /* Glassmorphism Metric Cards */
        [data-testid="stMetric"] {{
            background: #FFFFFF;
            border: 1px solid #F3F3F3;
            padding: 18px !important;
            border-radius: 12px !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.02);
        }}
        [data-testid="stMetricValue"] {{
            color: {DP_TEAL} !important;
            font-size: 1.6rem !important;
            font-weight: 400 !important;
        }}

        /* Action Button - Minimalist Teal */
        .stButton>button {{
            background: {DP_TEAL};
            color: white;
            border-radius: 8px;
            border: none;
            font-size: 0.85rem;
            font-weight: 400;
            padding: 8px 18px;
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
        if 'user_db' not in st.session_state:
            st.session_state.user_db = pd.DataFrame([{"email": "telmo.alves@docplanner.com", "password": "Memes0812", "role": "Admin"}])
        if 'master_data' not in st.session_state:
            st.session_state.master_data = pd.DataFrame(columns=["Date", "Volume", "SL", "AHT", "FTE", "Country"])
        if 'exception_logs' not in st.session_state:
            st.session_state.exception_logs = pd.DataFrame(columns=["Country", "Timestamp", "Agent", "Type", "Duration (Min)", "Notes"])

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    sync_from_cloud()

# 3. GLOBAL SETUP
DP_LOGO = "https://www.docplanner.com/img/logo-default-group-en.svg"
COUNTRIES = ["Spain", "Mexico", "Poland", "Germany", "Italy", "Brazil", "Colombia", "Turkey"]

# 4. LOGIN GATE
if not st.session_state.logged_in:
    _, center, _ = st.columns([1,1.5,1])
    with center:
        st.image(DP_LOGO, width=200)
        st.title("Sign in to WFM Workspace")
        e_in = st.text_input("Email")
        p_in = st.text_input("Password", type="password")
        if st.button("Continue", use_container_width=True):
            db = st.session_state.user_db
            match = db[(db['email'] == e_in) & (db['password'] == p_in)]
            if not match.empty:
                st.session_state.logged_in = True
                st.session_state.user_role = match.iloc[0]['role']
                st.session_state.current_email = match.iloc[0]['email']
                st.rerun()
            else: st.error("Invalid credentials.")
    st.stop()

# 5. NAVIGATION LOGIC
role = st.session_state.user_role
nav_dict = {
    "Dashboard": "Dashboard",
    "Import Data": "Import Data",
    "Forecasting": "Forecasting",
    "Exception Management": "Exceptions",
    "Capacity Planner (Erlang)": "Capacity Planner",
    "Reporting Center": "Reporting",
    "Admin Panel": "Admin Panel",
    "System Status": "System Status"
}

available_nav = ["Dashboard", "Forecasting"]
if role == "Admin": available_nav.insert(1, "Import Data")
if role in ["Admin", "Manager"]: available_nav.extend(["Exception Management", "Capacity Planner (Erlang)"])
if role == "Admin": available_nav.extend(["Reporting Center", "Admin Panel", "System Status"])

with st.sidebar:
    st.image(DP_LOGO, width=150)
    st.write(f"**{st.session_state.current_email}**")
    st.divider()
    
    menu = st.radio("Navigation Menu", available_nav)
    
    st.divider()
    view_mode = st.radio("Market Selection", ["All Markets", "Regional Select"])
    if view_mode == "Regional Select":
        selected_markets = st.multiselect("Active Markets", COUNTRIES, default=COUNTRIES)
    else: selected_markets = COUNTRIES
    
    if st.button("Sync Data", use_container_width=True):
        sync_from_cloud()
        st.toast("Database Synced")

# 6. ENGINES
def erlang_c(vol, aht, target_t, agents):
    intensity = (vol * aht) / 3600
    if agents <= intensity: return 0.0 
    sum_inv = sum([(intensity**i) / math.factorial(i) for i in range(int(agents))])
    numerator = (intensity**agents / math.factorial(int(agents))) * (agents / (agents - intensity))
    prob_w = numerator / (sum_inv + numerator)
    return 1 - (prob_w * math.exp(-(agents - intensity) * (target_t / aht)))

# 7. MODULES

if menu == "Dashboard":
    st.title("Performance Summary")
    df = st.session_state.master_data
    if not df.empty:
        df_f = df[df['Country'].isin(selected_markets)].copy()
        if not df_f.empty:
            for c in ['Volume', 'SL', 'AHT', 'FTE']: df_f[c] = pd.to_numeric(df_f[c], errors='coerce').fillna(0)
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Volume", f"{df_f['Volume'].sum():,.0f}")
            c2.metric("Weighted SL", f"{(df_f['Volume']*df_f['SL']).sum()/df_f['Volume'].sum():.1f}%")
            c3.metric("Weighted AHT", f"{int((df_f['Volume']*df_f['AHT']).sum()/df_f['Volume'].sum())}s")
            c4.metric("Actual FTE", f"{df_f['FTE'].sum():,.1f}")
            
            st.write("---")
            fig = px.line(df_f, x='Date', y='Volume', color='Country', template="plotly_white")
            fig.update_traces(line_color=DP_TEAL)
            st.plotly_chart(fig, use_container_width=True)

elif menu == "Import Data":
    st.title("Data Ingestion")
    target = st.selectbox("Assign Market", COUNTRIES)
    up = st.file_uploader("Upload CSV", type="csv")
    if up:
        new_df = pd.read_csv(up)
        new_df.columns = new_df.columns.str.strip()
        new_df['Country'] = target
        st.session_state.master_data = pd.concat([st.session_state.master_data[st.session_state.master_data['Country'] != target], new_df], ignore_index=True)
        conn.update(worksheet="master_data", data=st.session_state.master_data)
        st.success(f"Pushed {target} to Cloud")

elif menu == "Admin Panel":
    st.title("User Management")
    with st.form("new_u"):
        n_e = st.text_input("Email")
        n_p = st.text_input("Password")
        n_r = st.selectbox("Role", ["Admin", "Manager", "User"])
        if st.form_submit_button("Save User"):
            new_u = pd.DataFrame([{"email": n_e, "password": n_p, "role": n_r}])
            st.session_state.user_db = pd.concat([st.session_state.user_db, new_u], ignore_index=True)
            conn.update(worksheet="user_db", data=st.session_state.user_db)
            st.success("Cloud Updated")
    st.dataframe(st.session_state.user_db[['email', 'role']])

# (Rest of the logic remains the same)
