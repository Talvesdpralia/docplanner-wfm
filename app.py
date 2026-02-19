import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.io as pio
from datetime import datetime, timedelta
import math
import calendar
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
        
        .stApp {{
            font-family: 'Figtree', sans-serif !important;
            background: radial-gradient(circle at 10% 40%, rgba(0, 196, 167, 0.05), transparent 40%),
                        radial-gradient(circle at 90% 10%, rgba(1, 30, 65, 0.04), transparent 40%),
                        #f8fafc !important; 
        }}

        h1 {{ font-weight: 300 !important; font-size: 1.7rem !important; color: {DP_NAVY}; letter-spacing: -0.5px; }}
        h2, h3 {{ font-weight: 400 !important; font-size: 1.1rem !important; color: {DP_SLATE}; }}
        p, span, label {{ font-size: 13.5px !important; }}

        /* SIDEBAR GLASS */
        section[data-testid="stSidebar"] {{
            background: rgba(255, 255, 255, 0.1) !important;
            backdrop-filter: blur(40px) saturate(200%) !important;
            border-right: 1px solid rgba(255, 255, 255, 0.4) !important;
            box-shadow: 4px 0 24px rgba(0,0,0,0.02) !important;
        }}

        [data-testid="stSidebar"] div[role="radiogroup"] label > div:first-child {{ display: none !important; }}

        [data-testid="stSidebar"] div[role="radiogroup"] label {{
            background: transparent !important;
            padding: 6px 12px !important;
            margin-bottom: 2px !important;
            border-radius: 8px !important;
            transition: all 0.2s ease !important;
            color: {DP_NAVY} !important;
            font-weight: 400 !important;
            border-left: 3px solid transparent !important;
        }}
        
        [data-testid="stSidebar"] div[role="radiogroup"] label:hover {{ background: rgba(0, 196, 167, 0.04) !important; }}

        [data-testid="stSidebar"] div[role="radiogroup"] label[aria-checked="true"],
        [data-testid="stSidebar"] div[role="radiogroup"] label[data-checked="true"] {{
            background: rgba(0, 196, 167, 0.06) !important;
            border-left: 3px solid {DP_TEAL} !important;
            color: {DP_TEAL} !important;
            font-weight: 600 !important;
        }}

        div[role="radiogroup"] div[data-testid="stMarkdownContainer"] ~ div[aria-checked="true"] div:first-child,
        div[role="radiogroup"] div[data-testid="stMarkdownContainer"] ~ div[data-checked="true"] div:first-child {{
            background-color: {DP_TEAL} !important; border-color: {DP_TEAL} !important;
        }}

        /* PROMPT BOXES (NO GREY HALOS) */
        div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="select"] > div {{
            background-color: rgba(255, 255, 255, 0.9) !important;
            border: 1px solid rgba(0,0,0,0.03) !important;
            border-radius: 20px !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.02), 0 1px 2px rgba(0,0,0,0.02) !important;
            padding: 2px 8px !important;
            transition: box-shadow 0.2s ease !important;
        }}

        div[data-baseweb="input"]:focus-within, div[data-baseweb="select"] > div:focus-within {{
            box-shadow: 0 8px 20px rgba(0, 196, 167, 0.1) !important;
            border: 1px solid rgba(0, 196, 167, 0.4) !important;
        }}

        .stTextInput input, .stNumberInput input {{
            background-color: transparent !important; border: none !important; box-shadow: none !important; padding: 8px !important;
        }}

        /* METRICS & BUTTONS */
        [data-testid="stMetric"] {{
            background: rgba(255, 255, 255, 0.6) !important;
            backdrop-filter: blur(15px);
            border: 1px solid rgba(255, 255, 255, 0.8) !important;
            padding: 16px !important;
            border-radius: 16px !important;
            box-shadow: 0 4px 15px rgba(0,0,0,0.02) !important;
        }}

        .stButton>button {{
            background: {DP_TEAL} !important; color: white !important; border-radius: 20px !important;
            border: none !important; padding: 8px 24px !important; font-weight: 500 !important;
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
        
        md = conn.read(worksheet="master_data", ttl="0")
        if 'Country' not in md.columns: md = pd.DataFrame(columns=["Date", "Volume", "SL", "AHT", "FTE", "Country"])
        st.session_state.master_data = md
        
        el = conn.read(worksheet="exception_logs", ttl="0")
        if 'Country' not in el.columns: el = pd.DataFrame(columns=["Country", "Timestamp", "Agent", "Type", "Duration (Min)", "Notes"])
        st.session_state.exception_logs = el

        # NEW: Schedule Database
        sd = conn.read(worksheet="schedule_db", ttl="0")
        if 'Country' not in sd.columns: sd = pd.DataFrame(columns=["Country", "YearMonth", "Agent", "Time"] + [str(d) for d in range(1, 32)])
        st.session_state.schedule_db = sd
        
    except Exception:
        st.session_state.user_db = pd.DataFrame([{"email": "telmo.alves@docplanner.com", "password": "Memes0812", "role": "Admin"}])
        st.session_state.master_data = pd.DataFrame(columns=["Date", "Volume", "SL", "AHT", "FTE", "Country"])
        st.session_state.exception_logs = pd.DataFrame(columns=["Country", "Timestamp", "Agent", "Type", "Duration (Min)", "Notes"])
        st.session_state.schedule_db = pd.DataFrame(columns=["Country", "YearMonth", "Agent", "Time"] + [str(d) for d in range(1, 32)])

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
    sync_from_cloud()

# ==========================================
# 3. GLOBAL ASSETS
# ==========================================
DP_LOGO = "https://www.docplanner.com/img/logo-default-group-en.svg"
COUNTRIES = ["Spain", "Mexico", "Poland", "Germany", "Italy", "Brazil", "Colombia", "Turkey"]

nav_icons = {
    "Dashboard": "⟢", "Import Data": "⤓", "Forecasting": "📈", "Scheduling": "📅",
    "Exception Management": "⚠", "Capacity Planner (Erlang)": "◈", 
    "Reporting Center": "▤", "Admin Panel": "⚙", "System Status": "🛡"
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
    menu_options = ["Dashboard", "Import Data", "Forecasting", "Scheduling", "Exception Management", "Capacity Planner (Erlang)", "Reporting Center", "Admin Panel", "System Status"]
else:
    menu_options = ["Dashboard", "Forecasting", "Scheduling", "Exception Management", "Capacity Planner (Erlang)"]

with st.sidebar:
    st.image(DP_LOGO, width=130)
    st.markdown(f"**{st.session_state.current_email}**")
    
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
# 6. ENGINES & HELPERS
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

def generate_time_slots():
    return [f"{str(h).zfill(2)}:{str(m).zfill(2)}" for h in range(8, 20) for m in (0, 30)]

# ==========================================
# 7. MAIN MODULES
# ==========================================
if menu == "Dashboard":
    render_header("Performance Overview")
    df = st.session_state.master_data
    if not df.empty and 'Country' in df.columns:
        df_f = df[df['Country'].isin(selected_markets)].copy()
        if not df_f.empty:
            for c in ['Volume', 'SL', 'AHT', 'FTE']: df_f[c] = pd.to_numeric(df_f[c], errors='coerce').fillna(0)
            c1, c2, c3, c4 = st.columns(4)
            tot_v = df_f['Volume'].sum()
            c1.metric("Total Volume", f"{tot_v:,.0f}")
            c2.metric("Weighted SL%", f"{(df_f['Volume']*df_f['SL']).sum()/tot_v:.1f}%" if tot_v > 0 else "0%")
            c3.metric("Avg AHT", f"{int(df_f['AHT'].mean()) if tot_v > 0 else 0}s")
            c4.metric("Actual FTE", f"{df_f['FTE'].sum():,.1f}")
            st.plotly_chart(px.line(df_f, x='Date', y='Volume', color='Country', template="plotly_white"), use_container_width=True)
        else: st.info("No data matches the selected filters.")
    else: st.info("Cloud database is empty.")

elif menu == "Scheduling":
    render_header("Scheduling & Roster")
    
    tab1, tab2 = st.tabs(["🗓️ Team Roster", "⚙️ Manage & Upload Templates"])
    
    with tab1:
        st.write("### Agent Schedule View")
        s_db = st.session_state.schedule_db
        if not s_db.empty and 'Country' in s_db.columns:
            # Filter by market and get available agents
            market_db = s_db[s_db['Country'].isin(selected_markets)]
            agents = market_db['Agent'].dropna().unique().tolist()
            
            if agents:
                c1, c2 = st.columns([1, 3])
                selected_agent = c1.selectbox("Select Agent", agents)
                selected_ym = c1.selectbox("Select Month", market_db['YearMonth'].unique())
                
                # Fetch schedule for the specific agent and month
                agent_schedule = market_db[(market_db['Agent'] == selected_agent) & (market_db['YearMonth'] == selected_ym)].copy()
                
                if not agent_schedule.empty:
                    # Sort by Time properly
                    agent_schedule = agent_schedule.sort_values(by="Time")
                    # Clean columns for display (hide metadata)
                    display_cols = ["Time"] + [str(d) for d in range(1, 32) if str(d) in agent_schedule.columns]
                    display_df = agent_schedule[display_cols].set_index("Time")
                    
                    st.write(f"**Viewing Schedule:** {selected_agent} ({selected_ym})")
                    st.info("💡 Note: In future updates, Exceptions will dynamically overwrite blocks here in Red.")
                    
                    # Display editable dataframe for Managers/Admins
                    edited_df = st.data_editor(display_df, use_container_width=True)
                    
                    # Future implementation: save `edited_df` changes back to `schedule_db`
                else:
                    st.warning("No schedule found for this combination.")
            else:
                st.info("No agents found in the current schedule database. Please upload a schedule in the next tab.")
        else:
            st.info("Schedule database is empty.")

    with tab2:
        st.write("### 1. Download Blank Template")
        st.write("Columns represent days of the month. Rows represent 30-min intervals. Fill with: Phone, Chat, WhatsApp, Email.")
        col1, col2 = st.columns(2)
        y_sel = col1.number_input("Year", 2024, 2030, datetime.now().year)
        m_sel = col2.number_input("Month", 1, 12, datetime.now().month)
        
        if st.button("Generate Template"):
            days_in_month = calendar.monthrange(int(y_sel), int(m_sel))[1]
            times = generate_time_slots()
            # We create an empty structure. The user fills Agent Name and the day cells.
            df_temp = pd.DataFrame({"Agent": [""], "Time": [""]})
            
            # Populate the matrix to make it easy for the user
            rows = []
            for time in times:
                rows.append({"Agent": "Example_Agent_Name", "Time": time})
            df_temp = pd.DataFrame(rows)
            for d in range(1, days_in_month + 1): df_temp[str(d)] = ""
            
            csv = df_temp.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 Download CSV Template", data=csv, file_name=f"Schedule_Template_{y_sel}_{m_sel}.csv", mime="text/csv")
            
        st.divider()
        st.write("### 2. Upload Completed Schedule")
        target_country = st.selectbox("Assign to Market", COUNTRIES, key="sch_country")
        up_sch = st.file_uploader("Upload Populated Schedule CSV", type="csv")
        
        if up_sch:
            df_up = pd.read_csv(up_sch)
            df_up['Country'] = target_country
            df_up['YearMonth'] = f"{y_sel}-{str(m_sel).zfill(2)}"
            
            # Append to master schedule db
            st.session_state.schedule_db = pd.concat([st.session_state.schedule_db, df_up], ignore_index=True)
            conn.update(worksheet="schedule_db", data=st.session_state.schedule_db)
            st.success(f"Schedule for {target_country} ({y_sel}-{m_sel}) successfully uploaded to Cloud!")

elif menu == "Import Data":
    render_header("Data Ingestion")
    target = st.selectbox("Assign Data to Market", COUNTRIES)
    up = st.file_uploader("Drop Market CSV File", type="csv")
    if up:
        new_df = pd.read_csv(up)
        new_df.columns = new_df.columns.str.strip()
        new_df['Country'] = target
        if 'Country' not in st.session_state.master_data.columns: st.session_state.master_data = pd.DataFrame(columns=["Date", "Volume", "SL", "AHT", "FTE", "Country"])
        st.session_state.master_data = pd.concat([st.session_state.master_data[st.session_state.master_data['Country'] != target], new_df], ignore_index=True)
        conn.update(worksheet="master_data", data=st.session_state.master_data)
        st.success("Synchronized with Google Sheets.")

# [Remaining Modules: Exception, Erlang, Admin, System, Reporting remain identical to previous versions]
