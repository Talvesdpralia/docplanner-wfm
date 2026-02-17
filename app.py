import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import math
import io

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

# 2. ERLANG-C ENGINE
def calculate_erlang_c(total_calls_per_hour, aht_seconds, target_seconds, agents):
    intensity = (total_calls_per_hour * aht_seconds) / 3600
    if agents <= intensity: return 0.0 
    sum_inv = sum([(intensity**i) / math.factorial(i) for i in range(int(agents))])
    erlang_c_num = (intensity**agents / math.factorial(int(agents))) * (agents / (agents - intensity))
    prob_waiting = erlang_c_num / (sum_inv + erlang_c_num)
    service_level = 1 - (prob_waiting * math.exp(-(agents - intensity) * (target_seconds / aht_seconds)))
    return max(0, min(1, service_level))

# 3. INITIALIZATION
COUNTRIES = ["Spain", "Mexico", "Poland", "Germany", "Italy", "Brazil", "Colombia", "Turkey"]
DP_LOGO = "https://www.docplanner.com/img/logo-default-group-en.svg"

if 'master_data' not in st.session_state:
    st.session_state.master_data = pd.DataFrame(columns=["Date", "Volume", "SL", "AHT", "FTE", "Country"])
if 'exception_logs' not in st.session_state:
    st.session_state.exception_logs = pd.DataFrame(columns=["Country", "Timestamp", "Agent", "Type", "Duration (Min)", "Notes"])
if 'logged_in' not in st.session_state: 
    st.session_state.logged_in = False

# 4. USER DATABASE INITIALIZATION (CRITICAL)
if 'user_db' not in st.session_state:
    st.session_state.user_db = pd.DataFrame([
        {"email": "telmo.alves@docplanner.com", "password": "Memes0812", "role": "Admin"},
        {"email": "manager@docplanner.com", "password": "123", "role": "Manager"},
        {"email": "user@docplanner.com", "password": "123", "role": "User"}
    ])

# 5. LOGIN GATE
if not st.session_state.logged_in:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image(DP_LOGO, width=250)
        st.title("🛡️ WFM Access Control")
        email_in = st.text_input("Email Address")
        pass_in = st.text_input("Password", type="password")
        
        if st.button("Sign In", use_container_width=True):
            # Checking credentials against the user_db
            db = st.session_state.user_db
            user_match = db[(db['email'] == email_in) & (db['password'] == pass_in)]
            
            if not user_match.empty:
                st.session_state.logged_in = True
                st.session_state.user_role = user_match.iloc[0]['role']
                st.session_state.current_email = user_match.iloc[0]['email']
                st.rerun()
            else:
                st.error("Invalid email or password. Use: telmo.alves@docplanner.com / Memes0812")
    st.stop()

# 6. PERMISSIONS & NAVIGATION
role = st.session_state.user_role
nav_options = ["Dashboard", "Forecasting"]
if role in ["Admin", "Manager"]:
    nav_options.append("Exception Management")
    nav_options.append("Capacity Planner (Erlang)")
if role == "Admin":
    nav_options.insert(1, "Import Data")
    nav_options.append("Reporting Center")
    nav_options.append("Admin Panel")

# 7. SIDEBAR
with st.sidebar:
    st.image(DP_LOGO, width=200)
    st.markdown(f"**Account:** {st.session_state.current_email}")
    st.markdown(f"**Role:** {role}")
    st.divider()
    view_mode = st.radio("View Mode", ["Global View", "Single Country"])
    if view_mode == "Single Country":
        selected_countries = [st.selectbox("Select Market", COUNTRIES)]
    else:
        selected_countries = st.multiselect("Aggregate Regions", COUNTRIES, default=COUNTRIES)
    st.divider()
    menu = st.radio("Navigation", nav_options)
    if st.button("Logout"):
        st.session_state.logged_in = False
        st.rerun()

# 8. MODULES

if menu == "Admin Panel":
    st.title("👥 User Management Admin")
    with st.expander("➕ Create New User"):
        with st.form("new_user_form", clear_on_submit=True):
            n_email = st.text_input("User Email")
            n_pass = st.text_input("User Password")
            n_role = st.selectbox("Assign Role", ["Admin", "Manager", "User"])
            if st.form_submit_button("Create Account"):
                if n_email and n_pass:
                    new_entry = pd.DataFrame([{"email": n_email, "password": n_pass, "role": n_role}])
                    st.session_state.user_db = pd.concat([st.session_state.user_db, new_entry], ignore_index=True)
                    st.success(f"Account for {n_email} created!")
                else: st.warning("Please fill all fields.")
    st.write("### Registered Staff")
    st.dataframe(st.session_state.user_db[['email', 'role']], use_container_width=True)

elif menu == "Dashboard":
    st.title(f"📊 {view_mode} Dashboard")
    if not st.session_state.master_data.empty:
        df_f = st.session_state.master_data[st.session_state.master_data['Country'].isin(selected_countries)].copy()
        if not df_f.empty:
            df_f[['Volume', 'SL', 'AHT', 'FTE']] = df_f[['Volume', 'SL', 'AHT', 'FTE']].apply(pd.to_numeric, errors='coerce').fillna(0)
            tot_v = df_f['Volume'].sum()
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Volume", f"{tot_v:,.0f}")
            m2.metric("Weighted SL", f"{(df_f['Volume']*df_f['SL']).sum()/tot_v:.1f}%" if tot_v > 0 else "0%")
            m3.metric("Weighted AHT", f"{int((df_f['Volume']*df_f['AHT']).sum()/tot_v)}s" if tot_v > 0 else "0s")
            m4.metric("Actual FTE", f"{df_f['FTE'].sum():,.1f}")
            st.plotly_chart(px.line(df_f, x='Date', y='Volume', color='Country', title="Workload Volume"))
        else: st.warning("No data found for the selected regions.")
    else: st.info("Welcome. Go to 'Import Data' to upload your CSV.")

elif menu == "Import Data":
    st.title("📂 Data Management")
    sample_df = pd.DataFrame({"Date": ["2026-02-17"], "Volume": [1200], "SL": [80.0], "AHT": [280], "FTE": [15.5]})
    st.download_button("📥 Download Template", sample_df.to_csv(index=False).encode('utf-8'), "template.csv")
    st.divider()
    target = st.selectbox("Assign Market", COUNTRIES)
    up = st.file_uploader("Upload CSV", type="csv")
    if up:
        try:
            df = pd.read_csv(up)
        except:
            up.seek(0)
            df = pd.read_csv(up, encoding='latin1')
        df.columns = df.columns.str.strip()
        df['Country'] = target
        for col in ['Volume', 'SL', 'AHT', 'FTE']:
            if col not in df.columns: df[col] = 0
        st.session_state.master_data = pd.concat([st.session_state.master_data[st.session_state.master_data['Country'] != target], df], ignore_index=True)
        st.success(f"Database updated for {target}!")

elif menu == "Forecasting":
    st.title("📈 Forecast Analysis")
    if not st.session_state.master_data.empty:
        df_f = st.session_state.master_data[st.session_state.master_data['Country'].isin(selected_countries)].copy()
        st.plotly_chart(px.line(df_f, x='Date', y='Volume', color='Country', title="Historical Workload"))
    else: st.warning("Upload data first to see charts.")

elif menu == "Capacity Planner (Erlang)":
    st.title("🧮 Erlang-C Planner")
    
    col1, col2 = st.columns(2)
    with col1:
        vol_p = st.number_input("Peak Hour Volume", value=150)
        aht_p = st.number_input("AHT (Seconds)", value=300)
    with col2:
        sl_target = st.slider("Target SL %", 50, 99, 80) / 100
        t_target = st.number_input("Target Answer Time (Sec)", value=20)
        shrinkage = st.slider("Total Shrinkage %", 0, 50, 25) / 100
    if vol_p > 0:
        req_a = math.ceil((vol_p * aht_p) / 3600) + 1
        ach_sl = 0
        while ach_sl < sl_target and req_a < 500:
            ach_sl = calculate_erlang_c(vol_p, aht_p, t_target, req_a)
            if ach_sl < sl_target: req_a += 1
        st.divider()
        st.metric("Required Gross Headcount", f"{math.ceil(req_a / (1 - shrinkage))} FTE")

elif menu == "Exception Management":
    st.title("⚠️ Exception Tracking")
    with st.expander("📝 Log New Incident"):
        with st.form("exc_log", clear_on_submit=True):
            c_target = st.selectbox("Market", selected_countries)
            agent = st.text_input("Agent Name")
            etype = st.selectbox("Category", ["Sickness", "Late", "System Issue", "Meeting"])
            mins = st.number_input("Minutes Lost", value=30)
            if st.form_submit_button("Submit"):
                new_row = pd.DataFrame([[c_target, datetime.now().strftime("%Y-%m-%d %H:%M"), agent, etype, mins, ""]], columns=st.session_state.exception_logs.columns)
                st.session_state.exception_logs = pd.concat([st.session_state.exception_logs, new_row], ignore_index=True)
                st.success("Exception logged.")
    st.dataframe(st.session_state.exception_logs[st.session_state.exception_logs['Country'].isin(selected_countries)])

elif menu == "Reporting Center":
    st.title("📥 Export Center")
    if not st.session_state.master_data.empty:
        st.download_button("📥 Export Master CSV", data=st.session_state.master_data.to_csv(index=False).encode('utf-8'), file_name="Global_Master.csv")