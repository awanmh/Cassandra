import streamlit as st
import pandas as pd
import json
import logging
from datetime import datetime
from sqlalchemy.orm import Session
from core.database import SessionLocal, ScanResult, FoundSecret, FoundEndpoint

# --- Config & Setup ---
st.set_page_config(
    page_title="Cassandra Ultimate 2.1",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for "Premium" feel
st.markdown("""
<style>
    .metric-card {
        background-color: #0E1117;
        border: 1px solid #262730;
        border-radius: 8px;
        padding: 20px;
        color: white;
    }
    .stMetric label {
        color: #979A9F !important;
    }
    .stHeader {
        color: #FF4B4B; 
    }
    div[data-testid="stExpander"] div[role="button"] p {
        font-weight: bold;
        color: #FAFAFA;
    }
</style>
""", unsafe_allow_html=True)

def get_db_session():
    """Helper to get DB session"""
    return SessionLocal()

# --- Data Fetching Functions ---
def fetch_scan_results(db: Session):
    return db.query(ScanResult).all()

def fetch_secrets(db: Session):
    return db.query(FoundSecret).all()

def fetch_endpoints(db: Session):
    return db.query(FoundEndpoint).all()

def process_tech_data(scan_results):
    """Filter scan results for fingerprint data"""
    tech_data = []
    for res in scan_results:
        if res.scan_type == "Fingerprint":
            tech_data.append({
                "Target": res.target,
                "Technologies": res.details.get("all", []),
                "Frameworks": res.details.get("framework", []),
                "Servers": res.details.get("server", []),
                "Date": res.timestamp
            })
    return tech_data

def process_vuln_data(scan_results):
    """Filter for actual vulnerabilities (not info)"""
    vulns = []
    for res in scan_results:
        # Assuming non-INFO and non-Fingerprint are vulnerabilities or interesting findings
        if res.scan_type not in ["Fingerprint", "INFO"]:
            vulns.append({
                "Target": res.target,
                "Type": res.scan_type,
                "Severity": res.severity,
                "Details": str(res.details), # JSON to string for display
                "Date": res.timestamp
            })
    return vulns

# --- Main Dashboard ---
def main():
    st.sidebar.title("🕷️ Cassandra 2.1 BBE")
    st.sidebar.markdown("---")
    page = st.sidebar.radio("Navigation", ["Dashboard", "Raw Data", "About"])
    
    st.sidebar.markdown("---")
    st.sidebar.info("Status: **Active** ✅\n\nDatabase: **PostgreSQL**\n\nMode: **Stealth** 👻")

    # DB Connection
    try:
        db = get_db_session()
        scan_results = fetch_scan_results(db)
        found_secrets = fetch_secrets(db)
        found_endpoints = fetch_endpoints(db)
        db.close()
    except Exception as e:
        st.error(f"🔴 Database Connection Failed: {e}")
        return

    # Processing Data
    tech_data = process_tech_data(scan_results)
    vuln_data = process_vuln_data(scan_results)
    
    # METRICS Calculation
    total_targets = len(set([s.target for s in scan_results]))
    total_vulns = len(vuln_data)
    total_secrets = len(found_secrets)
    total_endpoints = len(found_endpoints)
    high_sev_vulns = len([v for v in vuln_data if v.get('Severity', '').lower() in ['high', 'critical']])

    if page == "Dashboard":
        st.title("🛰️ Command Center v2.1")
        st.markdown("### Real-time Intelligence Overview")
        
        # 1. Top Metrics Row
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Targets Engaged", total_targets, delta_color="off")
        col2.metric("Vulnerabilities", total_vulns, delta=f"{high_sev_vulns} Critical/High", delta_color="inverse")
        col3.metric("Secrets Leaked", total_secrets, delta_color="off")
        col4.metric("API Endpoints", total_endpoints, delta="Gold Mine")

        st.markdown("---")

        # 2. Main Tabs
        tab_tech, tab_vuln, tab_secret, tab_endpoints = st.tabs(["👁️ Recon (The Eyes)", "🧠 Vulns (The Brain)", "💰 Secrets (The Looter)", "📍 Endpoints (The Mine)"])

        with tab_tech:
            st.subheader("Target Technology Stack")
            if tech_data:
                df_tech = pd.DataFrame(tech_data)
                # Expand lists for better display if needed, or just show as is
                st.dataframe(
                    df_tech, 
                    column_config={
                        "Technologies": st.column_config.ListColumn("All Tech"),
                        "Frameworks": st.column_config.ListColumn("Frameworks"),
                        "Servers": st.column_config.ListColumn("Web Servers")
                    },
                    use_container_width=True
                )
            else:
                st.info("No fingerprinting data available yet. Run a scan!")

        with tab_vuln:
            st.subheader("Identified Security Flaws")
            if vuln_data:
                df_vuln = pd.DataFrame(vuln_data)
                
                # Color code severity
                def color_severity(val):
                    color = 'green'
                    if val.lower() == 'critical': color = 'red'
                    elif val.lower() == 'high': color = 'orange'
                    elif val.lower() == 'medium': color = 'yellow'
                    return f'color: {color}'

                st.dataframe(df_vuln.style.map(color_severity, subset=['Severity']), use_container_width=True)
            else:
                st.success("No vulnerabilities found (or no scans run). System clean.")

        with tab_secret:
            st.subheader("Exposed Secrets & Tokens")
            if found_secrets:
                data_secrets = [{
                    "Target": s.target,
                    "Type": s.secret_type,
                    "Value": s.value, 
                    "Source": s.file_source,
                    "Found At": s.timestamp
                } for s in found_secrets]
                
                df_secrets = pd.DataFrame(data_secrets)
                st.dataframe(df_secrets, use_container_width=True)
                
                if st.button("Export Secrets to CSV"):
                    csv = df_secrets.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "Download CSV",
                        csv,
                        "cassandra_secrets.csv",
                        "text/csv",
                        key='download-csv'
                    )
            else:
                st.info("No secrets harvested yet. The Looter is waiting.")
        
        with tab_endpoints:
            st.subheader("Discovered API Endpoints")
            if found_endpoints:
                data_eps = [{
                    "Target": e.target,
                    "Endpoint": e.endpoint,
                    "Source File": e.source_url,
                    "Found At": e.timestamp
                } for e in found_endpoints]
                st.dataframe(pd.DataFrame(data_eps), use_container_width=True)
            else:
                st.info("No endpoints extracted yet.")

    elif page == "Raw Data":
        st.header("🗃️ Raw Database View")
        
        option = st.selectbox("Select Table", ["Scan Results", "Found Secrets", "Found Endpoints"])
        
        if option == "Scan Results":
            st.dataframe(pd.DataFrame([vars(s) for s in scan_results]).drop(columns=['_sa_instance_state'], errors='ignore'))
        elif option == "Found Secrets":
            st.dataframe(pd.DataFrame([vars(s) for s in found_secrets]).drop(columns=['_sa_instance_state'], errors='ignore'))
        else:
            st.dataframe(pd.DataFrame([vars(e) for e in found_endpoints]).drop(columns=['_sa_instance_state'], errors='ignore'))

    elif page == "About":
        st.header("Cassandra Ultimate 2.1 BBE")
        st.markdown("""
        **Bug Bounty Edition**
        
        ### New Features v2.1
        - **Stealth Mode**: Proxy Rotation & Smart Delays.
        - **Compliance**: Scope Safety & Deny Lists.
        - **Real-time Alerts**: Discord Integration.
        - **Deep Extraction**: JS Endpoint Mining.
        """)

if __name__ == "__main__":
    main()
