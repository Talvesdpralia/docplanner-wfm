import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import math
from streamlit_gsheets import GSheetsConnection

# 1. UI & BRANDING CONFIGURATION
st.set_page_config(page_title="Docplanner WFM Pro", layout="wide", page_icon="🏥")

def apply_custom_design():
    st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Figtree:wght@300;400;600;700&display=swap');
        html, body, [class*="css"] { font-family: 'Figtree', sans-serif; background-color: #F8F9FA; }
        section[data-testid="stSidebar"] { background-color: #00c4a7 !important; }
        section[data-testid="stSidebar"] .stText, section[data-testid="stSidebar"] label,
        section[data-testid="stSidebar"] p, section[data-testid="stSidebar"] h1,
        section[data-testid="stSidebar"] h2 { color: white !important; font-weight: 600; }
        .stButton>button { background-color: #00c4a7; color: white; border-radius: 12px; border: none; padding: 10px 24px; font-weight: 600; }
        div[data-testid="stMetricValue"] { color: #00c4a7; font-weight: 700; }
        </style>
    """, unsafe_allow_html=True)

apply_custom_design()

# 2. DATABASE CONNECTION & SYNC
conn = st.connection("gsheets", type=GSheetsConnection)

def sync_from_cloud():
    """Fetch all data from Google Sheets into session state"""
    try:
        st.session_state.user_db = conn.read(worksheet="user_db", ttl="0")
        st.session_state.master_data = conn.read(worksheet="master_data", ttl="0")
        st.session_state.exception_logs = conn.read(worksheet="exception_logs", ttl="0")
    except Exception as e:
        # Fallback if sheet is empty or connection fails
        if 'user_db' not in st.session_state:
            st.session_state.user_db = pd.DataFrame([{"email": "telmo.alves@docplanner.com", "password": "Memes0812", "role": "Admin"}])
        if 'master_data' not in st.session_state:
            st.session_state.master_data = pd.DataFrame(columns=["Date", "Volume", "SL", "AHT", "FTE", "Country"])
        if 'exception_logs' not in st.session_state:
            st.session_state.exception_logs = pd.DataFrame(columns=["Country", "Timestamp", "Agent", "Type", "Duration (Min)", "Notes"])

# Initial Load
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    sync_from_cloud()

# 3. LOGIN GATE
DP_LOGO = "https://www.docplanner.com/img/logo-default-group-en.svg"
COUNTRIES = ["Spain", "Mexico", "Poland", "Germany", "Italy", "Brazil", "Colombia", "Turkey"]

if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image(DP_LOGO, width=250)
        st.title("🛡️ WFM Access Control")
        e_in = st.text_input("Email Address")
        p_in = st.text_input("Password", type="password")
        if st.button("Sign In", use_container_width=True):
            db = st.session_state.user_db
            match = db[(db['email'] == e_in) & (db['password'] == p_in)]
            if not match.empty:
                st.session_state.logged_in = True
                st.session_state.user_role = match.iloc[0]['role']
                st.session_state.current_email = match.iloc[0]['email']
                st.rerun()
            else: st.error("Invalid credentials.")
    st.stop()

# 4. NAVIGATION BUILDER
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
    view_mode = st.radio("View Mode", ["Global View", "Single Country"])
    if view_mode == "Single Country":
        selected_countries = [st.selectbox("Select Market", COUNTRIES)]
    else:
        selected_countries = st.multiselect("Aggregate Regions", COUNTRIES, default=COUNTRIES)
    st.divider()
    menu = st.radio("Navigation", nav_options)
    if st.sidebar.button("Sync with Cloud 🔄"):
        sync_from_cloud()
        st.toast("Data refreshed!")
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# 5. ENGINES
def calculate_erlang_c(total_calls_per_hour, aht_seconds, target_seconds, agents):
    intensity = (total_calls_per_hour * aht_seconds) / 3600
    if agents <= intensity: return 0.0 
    sum_inv = sum([(intensity**i) / math.factorial(i) for i in range(int(agents))])
    erlang_c_num = (intensity**agents / math.factorial(int(agents))) * (agents / (agents - intensity))
    prob_waiting = erlang_c_num / (sum_inv + erlang_c_num)
    service_level = 1 - (prob_waiting * math.exp(-(agents - intensity) * (target_seconds / aht_seconds)))
    return max(0, min(1, service_level))

# 6. MODULES

if menu == "System Status":
    st.title("🖥️ System Health")
    c1, c2, c3 = st.columns(3)
    c1.metric("Cloud Connection", "Connected")
    c2.metric("Database Rows", len(st.session_state.master_data))
    c3.metric("User Accounts", len(st.session_state.user_db))
    st.write("### Cloud Tables")
    st.write("User Database (Raw):", st.session_state.user_db)

elif menu == "Admin Panel":
    st.title("👥 User Management")
    with st.expander("➕ Add New User to Cloud"):
        with st.form("new_user"):
            n_email = st.text_input("Email")
            n_pass = st.text_input("Password")
            n_role = st.selectbox("Role", ["Admin", "Manager", "User"])
            if st.form_submit_button("Save to Google Sheets"):
                new_row = pd.DataFrame([{"email": n_email, "password": n_pass, "role": n_role}])
                st.session_state.user_db = pd.concat([st.session_state.user_db, new_row], ignore_index=True)
                conn.update(worksheet="user_db", data=st.session_state.user_db)
                st.success("User saved permanently!")
    st.dataframe(st.session_state.user_db[['email', 'role']], use_container_width=True)

elif menu == "Dashboard":
    st.title(f"📊 {view_mode}")
    df = st.session_state.master_data
    if not df.empty:
        df_f = df[df['Country'].isin(selected_countries)].copy()
        if not df_f.empty:
            for c in ['Volume', 'SL', 'AHT', 'FTE']: df_f[c] = pd.to_numeric(df_f[c], errors='coerce').fillna(0)
            tot_v = df_f['Volume'].sum()
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Volume", f"{tot_v:,.0f}")
            m2.metric("Weighted SL", f"{(df_f['Volume']*df_f['SL']).sum()/tot_v:.1f}%" if tot_v > 0 else "0%")
            m3.metric("Weighted AHT", f"{int((df_f['Volume']*df_f['AHT']).sum()/tot_v)}s" if tot_v > 0 else "0s")
            m4.metric("Actual FTE", f"{df_f['FTE'].sum():,.1f}")
            st.plotly_chart(px.line(df_f, x='Date', y='Volume', color='Country'))
    else: st.info("Database is empty. Import data to see results.")

elif menu == "Import Data":
    st.title("📂 Data Import")
    target = st.selectbox("Market", COUNTRIES)
    up = st.file_uploader("Upload CSV", type="csv")
    if up:
        new_data = pd.read_csv(up)
        new_data.columns = new_data.columns.str.strip()
        new_data['Country'] = target
        # Update Master Data
        st.session_state.master_data = pd.concat([st.session_state.master_data[st.session_state.master_data['Country'] != target], new_data], ignore_index=True)
        conn.update(worksheet="master_data", data=st.session_state.master_data)
        st.success(f"Data for {target} pushed to Cloud!")

elif menu == "Capacity Planner (Erlang)":
    st.title("🧮 Erlang Planner")
    col1, col2 = st.columns(2)
    with col1:
        v = st.number_input("Peak Hour Vol", value=150)
        a = st.number_input("AHT (Sec)", value=300)
    with col2:
        s = st.slider("Target SL%", 50, 99, 80) / 100
        t = st.number_input("Target Sec", value=20)
        sh = st.slider("Shrinkage%", 0, 50, 25) / 100
    if v > 0:
        req = math.ceil((v * a) / 3600) + 1
        ach = 0
        while ach < s and req < 500:
            ach = calculate_erlang_c(v, a, t, req)
            if ach < s: req += 1
        st.metric("Required FTE (Gross)", f"{math.ceil(req / (1 - sh))}")

elif menu == "Exception Management":
    st.title("⚠️ Exceptions")
    with st.form("exc"):
        ct = st.selectbox("Market", selected_countries)
        ag = st.text_input("Agent")
        et = st.selectbox("Type", ["Sickness", "Late", "Meeting"])
        dr = st.number_input("Min", value=30)
        if st.form_submit_button("Log and Push"):
            new_e = pd.DataFrame([[ct, datetime.now().strftime("%Y-%m-%d %H:%M"), ag, et, dr, ""]], columns=st.session_state.exception_logs.columns)
            st.session_state.exception_logs = pd.concat([st.session_state.exception_logs, new_e], ignore_index=True)
            conn.update(worksheet="exception_logs", data=st.session_state.exception_logs)
            st.success("Exception synced to Cloud!")
    st.dataframe(st.session_state.exception_logs)

elif menu == "Forecasting":
    st.title("📈 Forecasting")
    if not st.session_state.master_data.empty:
        st.plotly_chart(px.line(st.session_state.master_data, x='Date', y='Volume', color='Country'))

elif menu == "Reporting Center":
    st.title("📥 Reporting")
    st.download_button("Export Global Data", st.session_state.master_data.to_csv(index=False).encode('utf-8'), "Global_WFM.csv")
