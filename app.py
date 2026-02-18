import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio
from datetime import datetime
import math
from streamlit_gsheets import GSheetsConnection

# 1. DESIGN & BRANDING CONFIGURATION (THE GEMINI OVERHAUL)
st.set_page_config(page_title="Docplanner WFM Pro", layout="wide", page_icon="🏥")

# Define Docplanner Modern Color Palette
DP_TEAL = "#00c4a7"
DP_NAVY = "#011e41"
DP_MINT = "#e6f7f5"
DP_CORAL = "#ff5a5f"
DP_WHITE = "#FFFFFF"

# Set Custom Plotly Theme
pio.templates["docplanner"] = pio.templates["plotly_white"]
pio.templates["docplanner"].layout.colorway = [DP_TEAL, DP_NAVY, DP_CORAL, "#7e8083"]
pio.templates.default = "docplanner"

def apply_custom_design():
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Figtree:wght@300;400;500;600;700&display=swap');
        
        /* Global Styles & Mesh Background */
        .stApp {{
            background: radial-gradient(at 0% 0%, rgba(0, 196, 167, 0.08) 0px, transparent 50%),
                        radial-gradient(at 100% 100%, rgba(1, 30, 65, 0.05) 0px, transparent 50%),
                        #FFFFFF;
            font-family: 'Figtree', sans-serif !important;
        }}

        /* sidebar Modernization */
        section[data-testid="stSidebar"] {{
            background: linear-gradient(180deg, {DP_NAVY} 0%, #004d43 100%) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.1);
        }}
        section[data-testid="stSidebar"] .stMarkdown, section[data-testid="stSidebar"] label, section[data-testid="stSidebar"] p {{
            color: white !important;
        }}

        /* Glassmorphism Metric Cards */
        [data-testid="stMetric"] {{
            background: rgba(255, 255, 255, 0.7);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(0, 196, 167, 0.2);
            padding: 24px !important;
            border-radius: 20px !important;
            box-shadow: 0 10px 40px -10px rgba(0,0,0,0.05);
        }}
        [data-testid="stMetricValue"] {{
            color: {DP_TEAL} !important;
            font-size: 2.4rem !important;
            font-weight: 700 !important;
        }}

        /* Modern Input Styling */
        .stTextInput input, .stSelectbox div[data-baseweb="select"] {{
            border-radius: 12px !important;
            background-color: white !important;
            border: 1px solid rgba(0,0,0,0.1) !important;
        }}

        /* Glowing Material Buttons */
        .stButton>button {{
            background: linear-gradient(90deg, {DP_TEAL} 0%, #00dec0 100%);
            color: white;
            border-radius: 14px;
            border: none;
            padding: 14px 32px;
            font-weight: 600;
            box-shadow: 0 4px 20px rgba(0, 196, 167, 0.3);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}
        .stButton>button:hover {{
            box-shadow: 0 8px 25px rgba(0, 196, 167, 0.5);
            transform: translateY(-2px);
        }}

        /* Dataframe UI Refinement */
        [data-testid="stDataFrame"] {{
            border-radius: 16px !important;
            overflow: hidden !important;
            border: 1px solid rgba(0,0,0,0.05);
        }}
        </style>
    """, unsafe_allow_html=True)

apply_custom_design()

# 2. DATABASE CONNECTION & SYNC
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

# 3. GLOBAL VARIABLES
DP_LOGO = "https://www.docplanner.com/img/logo-default-group-en.svg"
COUNTRIES = ["Spain", "Mexico", "Poland", "Germany", "Italy", "Brazil", "Colombia", "Turkey"]

# 4. LOGIN GATE
if not st.session_state.logged_in:
    _, center, _ = st.columns([1,2,1])
    with center:
        st.image(DP_LOGO, width=280)
        st.title("🛡️ WFM Access Control")
        e_in = st.text_input("Email")
        p_in = st.text_input("Password", type="password")
        if st.button("Enter Workspace", use_container_width=True):
            db = st.session_state.user_db
            match = db[(db['email'] == e_in) & (db['password'] == p_in)]
            if not match.empty:
                st.session_state.logged_in = True
                st.session_state.user_role = match.iloc[0]['role']
                st.session_state.current_email = match.iloc[0]['email']
                st.rerun()
            else: st.error("Access denied. Please check your credentials.")
    st.stop()

# 5. NAVIGATION
role = st.session_state.user_role
nav_options = ["Dashboard", "Forecasting"]
if role in ["Admin", "Manager"]:
    nav_options.extend(["Exception Management", "Capacity Planner (Erlang)"])
if role == "Admin":
    nav_options.insert(1, "Import Data")
    nav_options.extend(["Reporting Center", "Admin Panel", "System Status"])

with st.sidebar:
    st.image(DP_LOGO, width=200)
    st.markdown(f"**Account:** {st.session_state.current_email}\n**Role:** {role}")
    st.divider()
    menu = st.radio("Navigation", nav_options)
    st.divider()
    view_mode = st.radio("Market View", ["Global", "Regional Select"])
    if view_mode == "Regional Select":
        selected_markets = st.multiselect("Markets", COUNTRIES, default=COUNTRIES)
    else: selected_markets = COUNTRIES
    
    if st.sidebar.button("Cloud Sync 🔄"):
        sync_from_cloud()
        st.toast("Database updated!")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

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
    st.title(f"📊 {view_mode} Insights")
    df = st.session_state.master_data
    if not df.empty:
        df_f = df[df['Country'].isin(selected_markets)].copy()
        if not df_f.empty:
            for c in ['Volume', 'SL', 'AHT', 'FTE']: df_f[c] = pd.to_numeric(df_f[c], errors='coerce').fillna(0)
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Volume", f"{df_f['Volume'].sum():,.0f}")
            c2.metric("Avg SL", f"{(df_f['Volume']*df_f['SL']).sum()/df_f['Volume'].sum():.1f}%")
            c3.metric("Avg AHT", f"{int((df_f['Volume']*df_f['AHT']).sum()/df_f['Volume'].sum())}s")
            c4.metric("Total FTE", f"{df_f['FTE'].sum():,.1f}")
            
            st.write("---")
            st.subheader("Workload vs Capacity Trends")
            fig = px.bar(df_f, x='Date', y='Volume', color='Country', title="Incoming Daily Volume")
            st.plotly_chart(fig, use_container_width=True)
            
            fig_fte = px.line(df_f, x='Date', y='FTE', color='Country', markers=True, title="Actual FTE Breakdown")
            st.plotly_chart(fig_fte, use_container_width=True)
    else: st.info("No data in cloud database. Please import market data.")

elif menu == "Import Data":
    st.title("📂 Data Gateway")
    target = st.selectbox("Market Destination", COUNTRIES)
    up = st.file_uploader("Select Market CSV", type="csv")
    if up:
        new_df = pd.read_csv(up)
        new_df.columns = new_df.columns.str.strip()
        new_df['Country'] = target
        st.session_state.master_data = pd.concat([st.session_state.master_data[st.session_state.master_data['Country'] != target], new_df], ignore_index=True)
        conn.update(worksheet="master_data", data=st.session_state.master_data)
        st.success(f"Market {target} synchronized with cloud database.")

elif menu == "Admin Panel":
    st.title("👥 User Authority")
    with st.form("new_u_form"):
        st.subheader("Create New Permanent Account")
        n_e = st.text_input("Email")
        n_p = st.text_input("Password")
        n_r = st.selectbox("Role", ["Admin", "Manager", "User"])
        if st.form_submit_button("Provision User"):
            new_u = pd.DataFrame([{"email": n_e, "password": n_p, "role": n_role}])
            st.session_state.user_db = pd.concat([st.session_state.user_db, new_u], ignore_index=True)
            conn.update(worksheet="user_db", data=st.session_state.user_db)
            st.success("User successfully added to Google Sheets.")
    st.dataframe(st.session_state.user_db[['email', 'role']], use_container_width=True)

elif menu == "Capacity Planner (Erlang)":
    st.title("🧮 Capacity Engine")
    
    col1, col2 = st.columns(2)
    with col1:
        v_h = st.number_input("Peak Hour Volume", value=150)
        a_s = st.number_input("AHT (Sec)", value=300)
    with col2:
        s_t = st.slider("Target SL%", 50, 99, 80) / 100
        sh = st.slider("Shrinkage %", 0, 50, 25) / 100
    if v_h > 0:
        req = math.ceil((v_h * a_s) / 3600) + 1
        ach = 0
        while ach < s_t and req < 500:
            ach = erlang_c(v_h, a_s, 20, req)
            if ach < s_t: req += 1
        st.metric("Recommended FTE", f"{math.ceil(req / (1 - sh))}")

elif menu == "Exception Management":
    st.title("⚠️ Live Exceptions")
    with st.form("exc_f"):
        mk = st.selectbox("Market", selected_markets)
        ag = st.text_input("Staff Name")
        et = st.selectbox("Category", ["Sickness", "System Issue", "Meeting"])
        dr = st.number_input("Duration (Min)", value=30)
        if st.form_submit_button("Broadcast Exception"):
            new_log = pd.DataFrame([[mk, datetime.now().strftime("%H:%M"), ag, et, dr, ""]], columns=st.session_state.exception_logs.columns)
            st.session_state.exception_logs = pd.concat([st.session_state.exception_logs, new_log], ignore_index=True)
            conn.update(worksheet="exception_logs", data=st.session_state.exception_logs)
            st.success("Exception pushed to global log.")
    st.dataframe(st.session_state.exception_logs)

elif menu == "System Status":
    st.title("🖥️ Core Infrastructure")
    c1, c2, c3 = st.columns(3)
    c1.metric("DB Link", "STABLE")
    c2.metric("Cloud Records", len(st.session_state.master_data))
    c3.metric("Latency", "LOW")
    st.write("Current Metadata:", st.session_state.user_db)
