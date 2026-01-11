import streamlit as st
import pandas as pd
import os
from pathlib import Path
import glob

# Config
st.set_page_config(page_title="Cassandra Ultimate", page_icon="🛡️", layout="wide")
DATA_DIR = Path(__file__).parent.parent / "data"

st.title("🛡️ Cassandra Ultimate Dashboard")
st.markdown("Automated Offensive Security Agent Results")

# Tabs
tab1, tab2, tab3 = st.tabs(["Subdomains", "Vulnerabilities", "Reports"])

with tab1:
    st.header("Discovered Subdomains")
    files = glob.glob(str(DATA_DIR / "**/subdomains.txt"))
    if files:
        # Assuming one main subdomain file or we list all
        latest_file = max(files, key=os.path.getctime)
        st.caption(f"Reading from: {latest_file}")
        
        try:
            with open(latest_file, "r") as f:
                subs = f.read().splitlines()
            st.dataframe(pd.DataFrame(subs, columns=["Subdomain"]), use_container_width=True)
            st.metric("Total Subdomains", len(subs))
        except Exception as e:
            st.error(f"Error reading file: {e}")
    else:
        st.info("No subdomain results found yet.")

with tab2:
    st.header("Critical Findings")
    
    col1, col2, col3 = st.columns(3)
    
    findings_files = {
        "SQLi": DATA_DIR / "sqli_findings.txt",
        "XSS": DATA_DIR / "xss_findings.txt",
        "Secrets": DATA_DIR / "secrets.txt"
    }
    
    for name, path in findings_files.items():
        if path.exists():
            with open(path, "r") as f:
                content = f.read()
            count = len(content.splitlines())
            if name == "SQLi":
                col1.error(f"{name}: {count} Issues")
                with st.expander(f"View {name} Details"):
                    st.text(content)
            elif name == "XSS":
                col2.error(f"{name}: {count} Issues")
                with st.expander(f"View {name} Details"):
                    st.text(content)
            else:
                col3.warning(f"{name}: {count} Leaks")
                with st.expander(f"View {name} Details"):
                    st.text(content)
        else:
            if name == "SQLi":
                col1.success(f"{name}: Clean")
            elif name == "XSS":
                col2.success(f"{name}: Clean")
            else:
                col3.success(f"{name}: Clean")

with tab3:
    st.header("Generate Report")
    if st.button("Download Full Report (Markdown)"):
        report = "# Cassandra Ultimate Scan Report\n\n"
        report += "## Summary\nScan completed.\n\n"
        
        # Aggregate findings
        for name, path in findings_files.items():
            if path.exists():
                report += f"### {name} Findings\n"
                with open(path, "r") as f:
                    report += "```\n" + f.read() + "\n```\n\n"
        
        st.download_button("Download MD", report, file_name="cassandra_report.md")
