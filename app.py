import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio
from datetime import datetime
import math
from streamlit_gsheets import GSheetsConnection

# 1. DESIGN & BRANDING CONFIGURATION
st.set_page_config(page_title="Docplanner WFM Pro", layout="wide", page_icon="🏥")

DP_TEAL = "#00c4a7"
DP_NAVY = "#011e41"

def apply_custom_design():
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Figtree:wght@300;400;500;600&display=swap');
        
        /* Global Background & Font */
        .stApp {{
            background: radial-gradient(at 0% 0%, rgba(0, 196, 167, 0.05) 0px, transparent 50%), #FFFFFF;
            font-family: 'Figtree', sans-serif !important;
        }}

        /* Thinner, Modern Headers */
        h1 {{ font-weight: 300 !important; font-size: 1.7rem !important; color: {DP_NAVY}; }}
        h2, h3 {{ font-weight: 400 !important; font-size: 1.1rem !important; color: #444; }}

        /* Glassmorphic Sidebar */
        section[data-testid="stSidebar"] {{
            background: rgba(255, 255, 255, 0.4) !important;
            backdrop-filter: blur(15px);
            border-right: 1px solid rgba(0, 196, 167, 0.1);
        }}

        /* Navigation Radio Styling */
        div.row-widget.stRadio > div {{ gap: 10px; }}
        div.row-widget.stRadio label {{
            background: transparent !important; /* No highlight */
            font-weight: 400 !important;
            font-size: 0.9rem !important;
            color: {DP_NAVY} !important;
            padding: 4px 0px !important;
        }}
        
        /* THE TEAL CIRCLE - Active Picker */
        div[role="radiogroup"] label[data-baseweb="radio"] div:first-child {{
            border-color: {DP_TEAL} !important;
        }}
        div[role="radiogroup"] label[data-baseweb="radio"] div:first-child div {{
            background-color: {DP_TEAL} !important;
        }}

        /* Glassmorphic Metric Cards */
        [data-testid="stMetric"] {{
            background: rgba(255, 255, 255, 0.6);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(0, 196, 167, 0.15);
            padding: 20px !important;
            border-radius: 16px !important;
            box-shadow: 0 8px 32px 0 rgba(0, 196, 167, 0.05);
        }}
        [data-testid="stMetricValue"] {{
            color: {DP_TEAL} !important;
            font-weight: 600 !important;
        }}

        /* Multiselect / Tag Styling */
        span[data-baseweb="tag"] {{
            background-color: {DP_TEAL} !important;
            border-radius: 6px !important;
        }}
        
        /* Modern Buttons */
        .stButton>button {{
            background: {DP_TEAL};
            color: white;
            border-radius: 10px;
            border: none;
            font-weight: 500;
            padding: 8px 20px;
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
        if 'user_db' not in st.session_state:
            st.session_state.user_db = pd.DataFrame([{"email": "telmo.alves@docplanner.com", "password": "Memes0812", "role": "Admin"}])
        if 'master_data' not in st.session_state:
            st.session_state.master_data = pd.DataFrame(columns=["Date", "Volume", "SL", "AHT", "FTE", "Country"])
        if 'exception_logs' not in st.session_state:
            st.session_state.exception_logs = pd.DataFrame(columns=["Country", "Timestamp", "Agent", "Type", "Duration (Min)", "Notes"])

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    sync_from_cloud()

# 3. SETUP & LOGO
DP_LOGO = "https://www.docplanner.com/img/logo-default-group-en.svg"
COUNTRIES = ["Spain", "Mexico", "Poland", "Germany", "Italy", "Brazil", "Colombia", "Turkey"]

# 4. LOGIN GATE
if not st.session_state.logged_in:
    _, center, _ = st.columns([1,1.5,1])
    with center:
        st.image(DP_LOGO, width=220)
        st.title("WFM Workspace")
        e_in = st.text_input("Work Email")
        p_in = st.text_input("Password", type="password")
        if st.button("Sign In", use_container_width=True):
            db = st.session_state.user_db
            match = db[(db['email'] == e_in) & (db['password'] == p_in)]
            if not match.empty:
                st.session_state.logged_in = True
                st.session_state.user_role = match.iloc[0]['role']
                st.session_state.current_email = match.iloc[0]['email']
                st.rerun()
            else: st.error("Authentication failed.")
    st.stop()

# 5. SIDEBAR NAVIGATION
role = st.session_state.user_role
nav_dict = {
    "Dashboard": "📊 Dashboard",
    "Import Data": "📥 Import Data",
    "Forecasting": "📈 Forecasting",
    "Exception Management": "🔔 Exceptions",
    "Capacity Planner (Erlang)": "🧮 Capacity",
    "Reporting Center": "📋 Reports",
    "Admin Panel": "👥 Admin Panel",
    "System Status": "🛡️ Status"
}

available_nav = ["Dashboard", "Forecasting"]
if role == "Admin": available_nav.insert(1, "Import Data")
if role in ["Admin", "Manager"]: available_nav.extend(["Exception Management", "Capacity Planner (Erlang)"])
if role == "Admin": available_nav.extend(["Reporting Center", "Admin Panel", "System Status"])

with st.sidebar:
    st.image(DP_LOGO, width=170)
    st.write(f"**{st.session_state.current_email}**")
    st.divider()
    
    menu_display = [nav_dict[opt] for opt in available_nav]
    choice = st.radio("Navigation", menu_display)
    menu = [k for k, v in nav_dict.items() if v == choice][0]
    
    st.divider()
    view_mode = st.radio("View", ["Global", "Regional Select"])
    if view_mode == "Regional Select":
        selected_markets = st.multiselect("Markets", COUNTRIES, default=COUNTRIES)
    else: selected_markets = COUNTRIES
    
    if st.button("Refresh Cloud 🔄", use_container_width=True):
        sync_from_cloud()
        st.rerun()

# 6. ERLANG-C ENGINE
def calculate_erlang_c(vol, aht, target_t, agents):
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
            tot_v = df_f['Volume'].sum()
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Volume", f"{tot_v:,.0f}")
            c2.metric("SL", f"{(df_f['Volume']*df_f['SL']).sum()/tot_v:.1f}%" if tot_v > 0 else "0%")
            c3.metric("AHT", f"{int((df_f['Volume']*df_f['AHT']).sum()/tot_v)}s" if tot_v > 0 else "0s")
            c4.metric("FTE", f"{df_f['FTE'].sum():,.1f}")
            st.write("---")
            st.plotly_chart(px.line(df_f, x='Date', y='Volume', color='Country', template="plotly_white"), use_container_width=True)
    else: st.info("Database is empty. Please upload data via 'Import Data'.")

elif menu == "Import Data":
    st.title("Data Ingestion")
    target = st.selectbox("Assign Market", COUNTRIES)
    up = st.file_uploader("Upload Market CSV", type="csv")
    if up:
        new_df = pd.read_csv(up)
        new_df.columns = new_df.columns.str.strip()
        new_df['Country'] = target
        st.session_state.master_data = pd.concat([st.session_state.master_data[st.session_state.master_data['Country'] != target], new_df], ignore_index=True)
        conn.update(worksheet="master_data", data=st.session_state.master_data)
        st.success(f"{target} successfully pushed to Cloud.")

elif menu == "Forecasting":
    st.title("Demand Forecast")
    if not st.session_state.master_data.empty:
        df_f = st.session_state.master_data[st.session_state.master_data['Country'].isin(selected_markets)]
        st.plotly_chart(px.area(df_f, x='Date', y='Volume', color='Country', title="Workload Forecast Trend"), use_container_width=True)
    else: st.warning("No historical data available for forecasting.")

elif menu == "Capacity Planner (Erlang)":
    st.title("Resource Planning (Erlang-C)")
    
    col1, col2 = st.columns(2)
    with col1:
        v_in = st.number_input("Peak Hour Calls", value=200)
        a_in = st.number_input("AHT (Sec)", value=300)
    with col2:
        s_target = st.slider("Target SL%", 50, 99, 80) / 100
        sh_in = st.slider("Shrinkage%", 0, 50, 20) / 100
    if v_in > 0:
        req = math.ceil((v_in * a_in) / 3600) + 1
        ach = 0
        while ach < s_target and req < 500:
            ach = calculate_erlang_c(v_in, a_in, 20, req)
            if ach < s_target: req += 1
        st.divider()
        st.metric("Required Headcount", f"{math.ceil(req / (1 - sh_in))} FTE")

elif menu == "Exception Management":
    st.title("Exception Log")
    with st.form("exc_f", clear_on_submit=True):
        m_in = st.selectbox("Market", selected_markets)
        ag_in = st.text_input("Agent")
        t_in = st.selectbox("Type", ["Sickness", "Late", "Technical", "Meeting"])
        d_in = st.number_input("Minutes", value=30)
        if st.form_submit_button("Log Exception"):
            new_e = pd.DataFrame([[m_in, datetime.now().strftime("%H:%M"), ag_in, t_in, d_in, ""]], columns=st.session_state.exception_logs.columns)
            st.session_state.exception_logs = pd.concat([st.session_state.exception_logs, new_e], ignore_index=True)
            conn.update(worksheet="exception_logs", data=st.session_state.exception_logs)
            st.success("Exception broadcasted to Cloud.")
    st.dataframe(st.session_state.exception_logs, use_container_width=True)

elif menu == "Admin Panel":
    st.title("User Management")
    with st.form("new_user"):
        n_e = st.text_input("Email")
        n_p = st.text_input("Password")
        n_r = st.selectbox("Role", ["Admin", "Manager", "User"])
        if st.form_submit_button("Create User"):
            new_u = pd.DataFrame([{"email": n_e, "password": n_p, "role": n_r}])
            st.session_state.user_db = pd.concat([st.session_state.user_db, new_u], ignore_index=True)
            conn.update(worksheet="user_db", data=st.session_state.user_db)
            st.success("User added to Cloud database.")
    st.write("### Current Users")
    st.dataframe(st.session_state.user_db[['email', 'role']], use_container_width=True)

elif menu == "System Status":
    st.title("Infrastructure Status")
    c1, c2, c3 = st.columns(3)
    c1.metric("API Connection", "Active")
    c2.metric("Cloud Records", len(st.session_state.master_data))
    c3.metric("Last Sync", datetime.now().strftime("%H:%M"))
    st.divider()
    st.write("Raw User DB (Debug Only):", st.session_state.user_db)

elif menu == "Reporting Center":
    st.title("Global Export")
    if not st.session_state.master_data.empty:
        st.download_button("Export All Master Data", st.session_state.master_data.to_csv(index=False).encode('utf-8'), "WFM_Global_Export.csv")
