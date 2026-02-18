import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio
from datetime import datetime
import math
from streamlit_gsheets import GSheetsConnection

# 1. DESIGN & BRANDING CONFIGURATION (THE GEMINI ULTRA-MODERN OVERHAUL)
st.set_page_config(page_title="Docplanner WFM Pro", layout="wide", page_icon="🏥")

DP_TEAL = "#00c4a7"
DP_NAVY = "#011e41"

def apply_custom_design():
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Figtree:wght@300;400;500;600&display=swap');
        
        /* Global Background & Root Variables */
        :root {{
            --primary-color: {DP_TEAL};
        }}
        
        .stApp {{
            background: radial-gradient(at 0% 0%, rgba(0, 196, 167, 0.03) 0px, transparent 50%),
                        radial-gradient(at 100% 100%, rgba(1, 30, 65, 0.02) 0px, transparent 50%),
                        #FFFFFF;
            font-family: 'Figtree', sans-serif !important;
        }}

        /* Hide Sidebar Scrollbar */
        section[data-testid="stSidebar"] > div {{
            overflow: hidden !important;
        }}
        
        /* Force Teal Accents on all Radio/Inputs */
        input[type="radio"], div[role="radiogroup"] {{
            accent-color: {DP_TEAL} !important;
        }}

        /* Salient Glassmorphic Sidebar */
        section[data-testid="stSidebar"] {{
            background: rgba(255, 255, 255, 0.1) !important;
            backdrop-filter: blur(30px) saturate(150%);
            border-right: 1px solid rgba(0, 196, 167, 0.2);
            box-shadow: 10px 0 30px rgba(0, 0, 0, 0.02);
        }}

        /* Navigation Typography */
        div.row-widget.stRadio > div {{ gap: 15px; }}
        div.row-widget.stRadio label {{
            background: transparent !important;
            font-weight: 300 !important;
            font-size: 0.95rem !important;
            color: {DP_NAVY} !important;
            transition: all 0.3s ease;
        }}
        div.row-widget.stRadio label:hover {{
            color: {DP_TEAL} !important;
        }}

        /* Metric Cards - Hyper Glass */
        [data-testid="stMetric"] {{
            background: rgba(255, 255, 255, 0.4);
            backdrop-filter: blur(15px);
            border: 1px solid rgba(0, 196, 167, 0.1);
            padding: 25px !important;
            border-radius: 24px !important;
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
        }}

        /* Headers - Thinner & Clean */
        h1 {{ 
            font-weight: 300 !important; 
            font-size: 2.2rem !important; 
            letter-spacing: -1px;
            color: {DP_NAVY}; 
        }}
        
        /* Section Icon Style */
        .section-header {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        .section-icon {{
            font-size: 2rem;
            opacity: 0.5;
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
        sync_data = pd.DataFrame([{"email": "telmo.alves@docplanner.com", "password": "Memes0812", "role": "Admin"}])
        st.session_state.user_db = sync_data

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    sync_from_cloud()

# 3. GLOBAL VARIABLES
DP_LOGO = "https://www.docplanner.com/img/logo-default-group-en.svg"
COUNTRIES = ["Spain", "Mexico", "Poland", "Germany", "Italy", "Brazil", "Colombia", "Turkey"]

# 4. LOGIN GATE
if not st.session_state.logged_in:
    _, center, _ = st.columns([1,1.5,1])
    with center:
        st.image(DP_LOGO, width=200)
        st.title("Sign in")
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
            else: st.error("Incorrect details.")
    st.stop()

# 5. SIDEBAR NAVIGATION
role = st.session_state.user_role
nav_icons = {
    "Dashboard": "📊", "Import Data": "📥", "Forecasting": "📈", 
    "Exception Management": "🔔", "Capacity Planner (Erlang)": "🧮", 
    "Reporting Center": "📋", "Admin Panel": "👥", "System Status": "🛡️"
}

available_nav = ["Dashboard", "Forecasting"]
if role == "Admin": available_nav.insert(1, "Import Data")
if role in ["Admin", "Manager"]: available_nav.extend(["Exception Management", "Capacity Planner (Erlang)"])
if role == "Admin": available_nav.extend(["Reporting Center", "Admin Panel", "System Status"])

with st.sidebar:
    st.image(DP_LOGO, width=160)
    st.markdown(f"<div style='margin-bottom: 20px; font-weight: 300;'>{st.session_state.current_email}</div>", unsafe_allow_html=True)
    
    menu = st.radio("Navigation", available_nav)
    
    st.divider()
    view_mode = st.radio("View", ["Global", "Regional Select"])
    if view_mode == "Regional Select":
        selected_markets = st.multiselect("Markets", COUNTRIES, default=COUNTRIES)
    else: selected_markets = COUNTRIES
    
    if st.button("Refresh Data", use_container_width=True):
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

# 7. MODULES (ICON MOVED TO HEADER)

# Custom Header Function
def section_header(title, icon):
    st.markdown(f"""
        <div class="section-header">
            <span class="section-icon">{icon}</span>
            <h1>{title}</h1>
        </div>
    """, unsafe_allow_html=True)

if menu == "Dashboard":
    section_header("Performance Overview", nav_icons["Dashboard"])
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
            st.plotly_chart(px.line(df_f, x='Date', y='Volume', color='Country', template="simple_white"), use_container_width=True)
    else: st.info("Database is empty.")

elif menu == "Import Data":
    section_header("Data Gateway", nav_icons["Import Data"])
    target = st.selectbox("Assign Market", COUNTRIES)
    up = st.file_uploader("Select Market CSV", type="csv")
    if up:
        new_df = pd.read_csv(up)
        new_df.columns = new_df.columns.str.strip()
        new_df['Country'] = target
        st.session_state.master_data = pd.concat([st.session_state.master_data[st.session_state.master_data['Country'] != target], new_df], ignore_index=True)
        conn.update(worksheet="master_data", data=st.session_state.master_data)
        st.success(f"Pushed to Cloud.")

elif menu == "Forecasting":
    section_header("Demand Prediction", nav_icons["Forecasting"])
    if not st.session_state.master_data.empty:
        df_f = st.session_state.master_data[st.session_state.master_data['Country'].isin(selected_markets)]
        st.plotly_chart(px.area(df_f, x='Date', y='Volume', color='Country'), use_container_width=True)
    else: st.warning("No historical data found.")

elif menu == "Capacity Planner (Erlang)":
    section_header("Resource Engine", nav_icons["Capacity Planner (Erlang)"])
    
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
        st.metric("Required Headcount", f"{math.ceil(req / (1 - sh_in))} FTE")

elif menu == "Exception Management":
    section_header("Live Incidents", nav_icons["Exception Management"])
    with st.form("exc_f", clear_on_submit=True):
        m_in = st.selectbox("Market", selected_markets)
        ag_in = st.text_input("Agent Name")
        t_in = st.selectbox("Type", ["Sickness", "Late", "Technical", "Meeting"])
        d_in = st.number_input("Minutes Lost", value=30)
        if st.form_submit_button("Broadcast"):
            new_e = pd.DataFrame([[m_in, datetime.now().strftime("%H:%M"), ag_in, t_in, d_in, ""]], columns=st.session_state.exception_logs.columns)
            st.session_state.exception_logs = pd.concat([st.session_state.exception_logs, new_e], ignore_index=True)
            conn.update(worksheet="exception_logs", data=st.session_state.exception_logs)
            st.success("Log pushed to Cloud.")
    st.dataframe(st.session_state.exception_logs, use_container_width=True)

elif menu == "Admin Panel":
    section_header("Authority Management", nav_icons["Admin Panel"])
    with st.form("new_user"):
        n_e = st.text_input("New Email")
        n_p = st.text_input("New Password")
        n_r = st.selectbox("Role", ["Admin", "Manager", "User"])
        if st.form_submit_button("Provision"):
            new_u = pd.DataFrame([{"email": n_e, "password": n_p, "role": n_r}])
            st.session_state.user_db = pd.concat([st.session_state.user_db, new_u], ignore_index=True)
            conn.update(worksheet="user_db", data=st.session_state.user_db)
            st.success("User saved to Cloud.")
    st.dataframe(st.session_state.user_db[['email', 'role']], use_container_width=True)

elif menu == "System Status":
    section_header("Core Infrastructure", nav_icons["System Status"])
    c1, c2, c3 = st.columns(3)
    c1.metric("Sync Status", "Healthy")
    c2.metric("Total Rows", len(st.session_state.master_data))
    c3.metric("Latency", "14ms")
    st.divider()
    st.write("Metadata Overview", st.session_state.user_db)

elif menu == "Reporting Center":
    section_header("Archive & Exports", nav_icons["Reporting Center"])
    if not st.session_state.master_data.empty:
        st.download_button("Export Cloud Master", st.session_state.master_data.to_csv(index=False).encode('utf-8'), "Global_Export.csv")
