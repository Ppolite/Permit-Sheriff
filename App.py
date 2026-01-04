import streamlit as st
import pandas as pd
import time
import hashlib
from datetime import datetime, timedelta
from fpdf import FPDF

# --- CONFIGURATION & SETUP ---
st.set_page_config(page_title="Permit Sheriff", page_icon="⭐", layout="wide")

# --- SESSION STATE INIT ---
if 'trigger' not in st.session_state:
    st.session_state['trigger'] = False
if 'selected_id' not in st.session_state:
    st.session_state['selected_id'] = None
if 'enforcement_log' not in st.session_state:
    st.session_state['enforcement_log'] = []

st.markdown(
    """
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #ff4b4b;
    }
    .status-ok {
        color: green;
        font-weight: bold;
    }
    .status-late {
        color: red;
        font-weight: bold;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
    }
</style>
""",
    unsafe_allow_html=True,
)

# --- MOCK DATA ---
def get_permit_data():
    return pd.DataFrame(
        [
            {
                "Permit ID": "MIA-24-001",
                "Address": "120 Ocean Dr, Miami",
                "Type": "Residential Reno",
                "Submitted": (datetime.now() - timedelta(days=45)).strftime(
                    "%Y-%m-%d"
                ),
                "Status": "Under Review",
                "Statute Limit": 30,
                "Days Open": 45,
                "Violation": True,
                "Refund Owed": "$450.00",
            },
            {
                "Permit ID": "MIA-24-009",
                "Address": "88 Biscayne Blvd",
                "Type": "Commercial HVAC",
                "Submitted": (datetime.now() - timedelta(days=5)).strftime(
                    "%Y-%m-%d"
                ),
                "Status": "In-Take",
                "Statute Limit": 10,
                "Days Open": 5,
                "Violation": False,
                "Refund Owed": "$0.00",
            },
            {
                "Permit ID": "JAX-24-882",
                "Address": "400 Bay St, Jax",
                "Type": "New Construction",
                "Submitted": (datetime.now() - timedelta(days=62)).strftime(
                    "%Y-%m-%d"
                ),
                "Status": "Comments Pending",
                "Statute Limit": 45,
                "Days Open": 62,
                "Violation": True,
                "Refund Owed": "$1,200.00",
            },
        ]
    )


def hash_data(content: str) -> str:
    """Simulates writing to blockchain by creating a SHA-256 hash."""
    return hashlib.sha256(content.encode()).hexdigest()


def generate_letter_text(permit_row: pd.Series) -> str:
    """Generate the legal demand letter text."""
    return f"""DEMAND FOR REMEDY PURSUANT TO FLORIDA STATUTE 553.79

TO: Building Official, City Permitting Department
RE: Permit Application #{permit_row['Permit ID']}
DATE: {datetime.now().strftime('%B %d, %Y')}

NOTICE OF STATUTORY VIOLATION

This letter serves as formal notice that the review period for Permit #{permit_row['Permit ID']} at {permit_row['Address']} has exceeded the mandatory statutory limit of {permit_row['Statute Limit']} days.

Current Status: {permit_row['Days Open']} days elapsed.

Pursuant to state law, we hereby demand:
1. Immediate refund of {permit_row['Refund Owed']} (10% of permit fees).
2. Immediate issuance of the permit or specific written cause for delay.

This notice has been cryptographically timestamped on-chain. Failure to respond may result in legal escalation.

Sincerely,
Permit Sheriff Enforcement Agent
"""


def create_pdf_letter(permit_row: pd.Series, letter_text: str, tx_hash: str) -> bytes:
    """Create a PDF with the letter text and blockchain proof footer."""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Header
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "PERMIT SHERIFF ENFORCEMENT", 0, 1, "C")
    pdf.line(10, 20, 200, 20)
    pdf.ln(10)

    # Body
    pdf.set_font("Arial", size=12)
    clean_text = letter_text.strip()
    pdf.multi_cell(0, 10, clean_text)

    # Footer (Blockchain Proof)
    pdf.ln(20)
    pdf.set_font("Courier", size=8)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 5, f"CRYPTOGRAPHIC PROOF: {tx_hash}", 0, 1)
    pdf.cell(0, 5, f"TIMESTAMP: {datetime.now().isoformat()}", 0, 1)

    # Return bytes
    pdf_bytes = pdf.output(dest="S").encode("latin-1", "ignore")
    return pdf_bytes


# --- UI LAYOUT ---

# Sidebar
st.sidebar.title("⭐ Permit Sheriff")
st.sidebar.markdown("**Organization:** Bayfront Builders LLC")
st.sidebar.markdown("**Jurisdiction:** Florida (Statewide)")
st.sidebar.markdown("**Active Mode:** Enforcement")
st.sidebar.divider()
mock_mode = st.sidebar.checkbox(
    "Demo Mode (Template Letters Only)", value=True,
    help="In a live deployment, AI-generated letters and real chain writes would be used."
)
st.sidebar.info("v1.0.0 – Hackathon Build")

# Main header
st.title("City Compliance Dashboard")
st.markdown("Track delays. Enforce statutes. **Get paid.**")

# Data
df = get_permit_data()
violations = df[df["Violation"] == True]
total_refunds = (
    violations["Refund Owed"].replace("[\$,]", "", regex=True).astype(float).sum()
)

# Top metrics
col1, col2, col3 = st.columns(3)
col1.metric("Active Permits", len(df))
col2.metric("Statute Violations", len(violations))
col3.metric("Recoverable Refunds", f"${total_refunds:,.2f}")

# Statute explainer
with st.expander("📚 Statute Profile – Florida Example"):
    st.markdown(
        """
- **Residential review limit:** 30 days  
- **Commercial review limit:** 45 days  
- **Remedy:** 10% fee refund + possible deemed-approval in some scenarios  
- **Primary statute:** Florida 553.79
"""
    )

st.divider()

# Permit table
st.subheader("📋 Permit Watchlist")


def highlight_violation(row):
    """Color rows by status: red = violation, yellow = near limit, green = OK."""
    styles = []
    ratio = row["Days Open"] / row["Statute Limit"]
    for _ in row.index:
        if row["Violation"]:
            styles.append("background-color: #ffcccc")  # red
        elif ratio > 0.8:
            styles.append("background-color: #fff4cc")  # yellow
        else:
            styles.append("background-color: #ccffcc")  # green
    return styles


st.dataframe(
    df.style.apply(highlight_violation, axis=1),
    use_container_width=True,
    hide_index=True,
)

st.divider()

# Enforcement center
st.subheader("🚨 Enforcement Action Center")

col_left, col_right = st.columns([1, 2])

selected_permit_id = None
target_permit = None

with col_left:
    st.write("Select a violation to enforce:")
    if violations.empty:
        st.warning("🎉 No active statute violations detected today.")
    else:
        selected_permit_id = st.selectbox("Select Permit ID", violations["Permit ID"])
        target_permit = df[df["Permit ID"] == selected_permit_id].iloc[0]

        st.info(
            f"**Target:** {target_permit['Address']}\n\n"
            f"**Overdue:** {target_permit['Days Open']} days "
            f"(Limit: {target_permit['Statute Limit']} days)\n\n"
            f"**Estimated Refund Owed:** {target_permit['Refund Owed']}\n\n"
            "**Basis:** Florida Statute 553.79"
        )

        if st.button("⚡ TRIGGER SHERIFF", type="primary"):
            st.session_state["trigger"] = True
            st.session_state["selected_id"] = selected_permit_id

with col_right:
    # Only fire process if trigger is set and IDs line up
    if (
        selected_permit_id is not None
        and st.session_state.get("trigger")
        and st.session_state.get("selected_id") == selected_permit_id
        and target_permit is not None
    ):
        # 1. The Processing Animation
        with st.status("🚀 Sheriff Agent Active...", expanded=True) as status:
            st.write("🔍 **Step 1:** Checking State Statutes (FL-553.79)...")
            time.sleep(1)
            st.write("✅ **Confirmed:** City is past legal review limit.")

            st.write("🤖 **Step 2:** Generating Legal Demand Letter...")
            time.sleep(1)
            letter_text = generate_letter_text(target_permit)
            st.write("✅ **Drafted:** Legal tone and statute references applied.")

            st.write("⛓️ **Step 3:** Notarizing on Chain...")
            time.sleep(1)
            tx_hash = hash_data(letter_text + str(time.time()))
            st.write(f"✅ **Immutable Proof Created:** `{tx_hash[:20]}...`")

            status.update(
                label="⚖️ Enforcement Package Ready – City is now on the clock",
                state="complete",
                expanded=True,
            )

        # 2. Letter preview
        st.markdown("### 📜 Generated Demand Letter")
        st.text_area("Preview", letter_text, height=220)

        st.success(f"Proof of violation recorded on-chain. Hash: {tx_hash}")

        # 3. PDF generation & download
        pdf_data = create_pdf_letter(target_permit, letter_text, tx_hash)
        st.download_button(
            label="🔥 Serve Legal Notice (Download PDF)",
            data=pdf_data,
            file_name=f"LEGAL_DEMAND_{selected_permit_id}.pdf",
            mime="application/pdf",
        )

        # 4. Log enforcement action in history
        st.session_state["enforcement_log"].append(
            {
                "Permit ID": selected_permit_id,
                "Address": target_permit["Address"],
                "Time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Hash": tx_hash[:12] + "...",
            }
        )

        # Reset trigger so it doesn't rerun on every refresh
        st.session_state["trigger"] = False

        # Start over button
        if st.button("Start Over"):
            st.session_state["trigger"] = False
            st.session_state["selected_id"] = None
            st.rerun()
    else:
        st.markdown(
            """
            <div style="text-align: center; color: gray; padding: 50px;
                        border: 2px dashed #ccc; border-radius: 10px;">
                Waiting for target selection...
            </div>
            """,
            unsafe_allow_html=True,
        )

# Enforcement history
st.markdown("### 📂 Enforcement History")
if st.session_state["enforcement_log"]:
    st.table(pd.DataFrame(st.session_state["enforcement_log"]))
else:
    st.caption("No enforcement actions recorded in this session yet.")
