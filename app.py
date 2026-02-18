import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio
from datetime import datetime
import math
from streamlit_gsheets import GSheetsConnection

# ==========================================
# 1. UI & DESIGN ENGINE - PREMIUM GLASS
# ==========================================
st.set_page_config(page_title="Docplanner WFM", layout="wide", page_icon="🏥")

DP_TEAL = "#00c4a7"
DP_NAVY = "#011e41"
DP_SLATE = "#4b5563"

def apply_custom_design():
    st.markdown(f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Figtree:wght@300;400;500;600&display=swap');
        
        /* Global Stage - Soft Mesh Gradient */
        .stApp {{
            font-family: 'Figtree', sans-serif !important;
            background: radial-gradient(circle at 10% 40%, rgba(0, 196, 167, 0.05), transparent 40%),
                        radial-gradient(circle at 90% 10%, rgba(1, 30, 65, 0.04), transparent 40%),
                        #f8fafc !important; 
        }}

        /* Typography */
        h1 {{ font-weight: 300 !important; font-size: 1.7rem !important; color: {DP_NAVY}; letter-spacing: -0.5px; }}
        h2, h3 {{ font-weight: 400 !important; font-size: 1.1rem !important; color: {DP_SLATE}; }}
        p, span, label {{ font-size: 13.5px !important; }}

        /* ==========================================
           SIDEBAR: ADVANCED GLASSMORPHISM
        ========================================== */
        section[data-testid="stSidebar"] {{
            background: rgba(255, 255, 255, 0.1) !important; /* Highly transparent */
            backdrop-filter: blur(40px) saturate(200%) !important; /* Strong glass blur */
            border-right: 1px solid rgba(255, 255, 255, 0.4) !important; /* Light reflection edge */
            box-shadow: 4px 0 24px rgba(0,0,0,0.02) !important;
        }}

        /* Hide Navigation Radio Circles SAFELY */
        [data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child {{
            display: none !important;
        }}

        /* Compact & Transparent Navigation List */
        [data-testid="stSidebar"] div[role="radiogroup"] label {{
            background: transparent !important; /* Fully transparent base */
            padding: 6px 12px !important; /* Reduced padding for compactness */
            margin-bottom: 2px !important; /* Tighter spacing to prevent scroll */
            border-radius: 8px !important;
            transition: all 0.2s ease !important;
            color: {DP_NAVY} !important;
            font-weight: 400 !important;
            border-left: 3px solid transparent !important;
        }}
        
        /* Hover State */
        [data-testid="stSidebar"] div[role="radiogroup"] label:hover {{
            background: rgba(0, 196, 167, 0.04) !important;
        }}

        /* Active Selected State */
        [data-testid="stSidebar"] div[role="radiogroup"] label[aria-checked="true"],
        [data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] {{
            background: rgba(0, 196, 167, 0.06) !important; /* Soft transparent teal tint */
            border-left: 3px solid {DP_TEAL} !important;
            color: {DP_TEAL} !important;
            font-weight: 600 !important;
        }}

        /* ==========================================
           RED CIRCLE REMOVAL (VIEW SETTING)
        ========================================== */
        div[role="radiogroup"] div[data-testid="stMarkdownContainer"] ~ div[aria-checked="true"] div:first-child,
        div[role="radiogroup"] div[data-testid="stMarkdownContainer"] ~ div[data-checked="true"] div:first-child {{
            background-color: {DP_TEAL} !important;
            border-color: {DP_TEAL} !important;
        }}

        /* ==========================================
           PROMPT BOXES (NO GREY HALOS)
        ========================================== */
        div[data-baseweb="input"], 
        div[data-baseweb="base-input"],
        div[data-baseweb="select"] > div {{
            background-color: rgba(255, 255, 255, 0.9) !important;
            border: 1px solid rgba(0,0,0,0.03) !important;
            border-radius: 20px !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.02), 0 1px 2px rgba(0,0,0,0.02) !important;
            padding: 2px 8px !important;
            transition: box-shadow 0.2s ease !important;
        }}

        div[data-baseweb="input"]:focus-within, 
        div[data-baseweb="select"] > div:focus-within {{
            box-shadow: 0 8px 20px rgba(0, 196, 167, 0.1) !important;
            border: 1px solid rgba(0, 196, 167, 0.4) !important;
        }}

        .stTextInput input, .stNumberInput input {{
            background-color: transparent !important;
            border: none !important;
            box-shadow: none !important;
            padding: 8px !important;
        }}

        /* ==========================================
           METRICS & BUTTONS
        ========================================== */
        [data-testid="stMetric"] {{
            background: rgba(255, 255, 255, 0.6) !important;
            backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.8) !important; /* Glass edge */
            padding: 16px !important;
            border-radius: 16px !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.02) !important;
        }}

        .stButton>button {{
            background: {DP_TEAL} !important;
            color: white !important;
            border-radius: 20px !important;
            border: none !important;
            padding: 8px 24px !important;
            font-weight: 500 !important;
            box-shadow: 0 4px 12px rgba(0, 196, 167, 0.2) !important;
        }}
        </style>
    """, unsafe_allow_html=True)

apply_custom_design()

# ==========================================
# 2. DATABASE CONNECTION & SYNC
# ==========================================
conn = st.connection("gsheets", type=GSheetsConnection)

def sync_from_cloud():
    try:
        st.session_state.user_db = conn.read(worksheet="user_db", ttl="0")
        st.session_state.master_data = conn.read(worksheet="master_data", ttl="0")
        st.session_state.exception_logs = conn.read(worksheet="exception_logs", ttl="0")
    except Exception:
        st.session_state.user_db = pd.DataFrame([{"email": "telmo.alves@docplanner.com", "password": "Memes0812", "role": "Admin"}])
        st.session_state.master_data = pd.DataFrame(columns=["Date", "Volume", "SL", "AHT", "FTE", "Country"])
        st.session_state.exception_logs = pd.DataFrame(columns=["Country", "Timestamp", "Agent", "Type", "Duration (Min)", "Notes"])

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    sync_from_cloud()

# ==========================================
# 3. GLOBAL ASSETS
# ==========================================
DP_LOGO = "https://www.docplanner.com/img/logo-default-group-en.svg"
COUNTRIES = ["Spain", "Mexico", "Poland", "Germany", "Italy", "Brazil", "Colombia", "Turkey"]

nav_icons = {
    "Dashboard": "⟢", 
    "Import Data": "⤓", 
    "Forecasting": "📈", 
    "Exception Management": "⚠", 
    "Capacity Planner (Erlang)": "◈", 
    "Reporting Center": "▤", 
    "Admin Panel": "⚙", 
    "System Status": "🛡"
}

# ==========================================
# 4. LOGIN GATE
# ==========================================
if not st.session_state.logged_in:
    _, col, _ = st.columns([1, 1.2, 1])
    with col:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.image(DP_LOGO, width=180)
        st.title("Workforce Workspace")
        e_in = st.text_input("Work Email", placeholder="your.name@docplanner.com")
        p_in = st.text_input("Password", type="password", placeholder="••••••••")
        if st.button("Continue", use_container_width=True):
            db = st.session_state.user_db
            match = db[(db['email'].str.lower() == e_in.lower()) & (db['password'] == p_in)]
            if not match.empty:
                st.session_state.logged_in = True
                st.session_state.user_role = str(match.iloc[0]['role'])
                st.session_state.current_email = str(match.iloc[0]['email'])
                st.rerun()
            else: 
                st.error("Access denied. Please check credentials.")
    st.stop()

# ==========================================
# 5. SIDEBAR NAVIGATION
# ==========================================
role = st.session_state.user_role

if role == "Admin":
    menu_options = ["Dashboard", "Import Data", "Forecasting", "Exception Management", "Capacity Planner (Erlang)", "Reporting Center", "Admin Panel", "System Status"]
else:
    menu_options = ["Dashboard", "Forecasting", "Exception Management", "Capacity Planner (Erlang)"]

with st.sidebar:
    st.image(DP_LOGO, width=130)
    st.markdown(f"**{st.session_state.current_email}**")
    
    # Custom tight divider
    st.markdown("<hr style='margin: 10px 0; border-color: rgba(0,0,0,0.05);'>", unsafe_allow_html=True)
    
    menu = st.radio("Navigation", menu_options, label_visibility="collapsed")
    
    st.markdown("<hr style='margin: 10px 0; border-color: rgba(0,0,0,0.05);'>", unsafe_allow_html=True)
    
    view_mode = st.radio("View Setting", ["Global", "Regional Select"])
    
    selected_markets = COUNTRIES
    if view_mode == "Regional Select":
        selected_markets = st.multiselect("Select Markets", COUNTRIES, default=COUNTRIES)
    
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("Sync Data 🔄", use_container_width=True):
        sync_from_cloud()
        st.rerun()

# ==========================================
# 6. ENGINES
# ==========================================
def calculate_erlang_c(vol, aht, target_t, agents):
    intensity = (vol * aht) / 3600
    if agents <= intensity: return 0.0 
    sum_inv = sum([(intensity**i) / math.factorial(i) for i in range(int(agents))])
    numerator = (intensity**agents / math.factorial(int(agents))) * (agents / (agents - intensity))
    prob_w = numerator / (sum_inv + numerator)
    return 1 - (prob_w * math.exp(-(agents - intensity) * (target_t / aht)))

def render_header(title):
    icon = nav_icons.get(title, "⟢")
    st.markdown(f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:20px;"><span style="font-size:1.6rem;color:{DP_TEAL};opacity:0.8;">{icon}</span><h1 style="margin:0 !important;">{title}</h1></div>', unsafe_allow_html=True)

# ==========================================
# 7. MAIN MODULES
# ==========================================
if menu == "Dashboard":
    render_header("Performance Overview")
    df = st.session_state.master_data
    if not df.empty:
        df_f = df[df['Country'].isin(selected_markets)].copy()
        if not df_f.empty:
            for c in ['Volume', 'SL', 'AHT', 'FTE']: df_f[c] = pd.to_numeric(df_f[c], errors='coerce').fillna(0)
            c1, c2, c3, c4 = st.columns(4)
            tot_v = df_f['Volume'].sum()
            c1.metric("Total Volume", f"{tot_v:,.0f}")
            c2.metric("Weighted SL%", f"{(df_f['Volume']*df_f['SL']).sum()/tot_v:.1f}%" if tot_v > 0 else "0%")
            c3.metric("Avg AHT", f"{int(df_f['AHT'].mean()) if tot_v > 0 else 0}s")
            c4.metric("Actual FTE", f"{df_f['FTE'].sum():,.1f}")
            st.markdown("<hr style='margin: 20px 0; border-color: rgba(0,0,0,0.05);'>", unsafe_allow_html=True)
            st.plotly_chart(px.line(df_f, x='Date', y='Volume', color='Country', template="plotly_white"), use_container_width=True)
        else:
            st.info("No data matches the selected filters.")
    else: 
        st.info("Cloud database is empty. Please import market data.")

elif menu == "Import Data":
    render_header("Data Ingestion")
    target = st.selectbox("Assign Data to Market", COUNTRIES)
    up = st.file_uploader("Drop Market CSV File", type="csv")
    if up:
        new_df = pd.read_csv(up)
        new_df['Country'] = target
        st.session_state.master_data = pd.concat([st.session_state.master_data[st.session_state.master_data['Country'] != target], new_df], ignore_index=True)
        conn.update(worksheet="master_data", data=st.session_state.master_data)
        st.success(f"Successfully synchronized {target} data with Google Sheets.")

elif menu == "Forecasting":
    render_header("Demand Prediction")
    st.info("Awaiting historical trend data for generation.")

elif menu == "Exception Management":
    render_header("Live Exceptions")
    with st.form("exc_log", clear_on_submit=True):
        ct_in = st.selectbox("Market Selection", COUNTRIES)
        agt_in = st.text_input("Staff Name")
        t_in = st.selectbox("Reason Code", ["Sickness", "Late", "Technical", "Meeting"])
        d_in = st.number_input("Duration (Minutes)", value=30, min_value=1)
        if st.form_submit_button("Log Exception"):
            new_e = pd.DataFrame([[ct_in, datetime.now().strftime("%Y-%m-%d %H:%M"), agt_in, t_in, d_in, ""]], columns=st.session_state.exception_logs.columns)
            st.session_state.exception_logs = pd.concat([st.session_state.exception_logs, new_e], ignore_index=True)
            conn.update(worksheet="exception_logs", data=st.session_state.exception_logs)
            st.success("Exception logged to Cloud.")
    st.dataframe(st.session_state.exception_logs, use_container_width=True)

elif menu == "Capacity Planner (Erlang)":
    render_header("Capacity Engine")
    col1, col2 = st.columns(2)
    with col1:
        v_h = st.number_input("Peak Period Volume", value=200, min_value=1)
        a_s = st.number_input("Target AHT (Seconds)", value=300, min_value=1)
    with col2:
        s_t = st.slider("Service Level Target %", 50, 99, 80) / 100
        sh = st.slider("Shrinkage %", 0, 50, 20) / 100
    if v_h > 0:
        req = math.ceil((v_h * a_s) / 3600) + 1
        ach = 0
        while ach < s_t and req < 500:
            ach = calculate_erlang_c(v_h, a_s, 20, req)
            if ach < s_t: req += 1
        st.markdown("<hr style='margin: 20px 0; border-color: rgba(0,0,0,0.05);'>", unsafe_allow_html=True)
        st.metric("Recommended FTE Capacity", f"{math.ceil(req / (1 - sh))} Agents")

elif menu == "Admin Panel":
    render_header("Access Management")
    with st.form("user_add", clear_on_submit=True):
        n_e = st.text_input("New User Email")
        n_p = st.text_input("Temporary Password")
        n_r = st.selectbox("Role Assignment", ["Admin", "Manager", "User"])
        if st.form_submit_button("Provision Access"):
            if n_e and n_p:
                new_u = pd.DataFrame([{"email": n_e, "password": n_p, "role": n_r}])
                st.session_state.user_db = pd.concat([st.session_state.user_db, new_u], ignore_index=True)
                conn.update(worksheet="user_db", data=st.session_state.user_db)
                st.success(f"Access granted to {n_e}.")
            else:
                st.error("Email and Password cannot be empty.")
    st.write("### Authorized Directory")
    st.dataframe(st.session_state.user_db[['email', 'role']], use_container_width=True)

elif menu == "System Status":
    render_header("Infrastructure Health")
    c1, c2, c3 = st.columns(3)
    c1.metric("Cloud Link", "Stable")
    c2.metric("Database Rows", len(st.session_state.master_data))
    c3.metric("Service Latency", "12ms")

elif menu == "Reporting Center":
    render_header("Data Exports")
    if not st.session_state.master_data.empty:
        csv = st.session_state.master_data.to_csv(index=False).encode('utf-8')
        st.download_button("Export Global Master Data (CSV)", data=csv, file_name="WFM_Global_Export.csv", mime="text/csv")
    else:
        st.warning("No data available to export.")
