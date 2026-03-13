"""
MGIS Outbound Declaration Generator - Streamlit UI

Focused on Outbound Shipments Only.
Inbound processing is handled separately.

Design Principles:
1. UI code has no business logic
2. All state managed through pipeline and session_state
3. Progress callbacks enable responsive UI
4. Error handling shows user-friendly messages
5. Supports both local (.env) and deployed (st.secrets) configurations
"""

import streamlit as st
import pandas as pd
import tempfile
import os
import sys
from datetime import date
from typing import Optional

# ============================================================================
# Page Configuration (MUST BE FIRST)
# ============================================================================

st.set_page_config(
    page_title="MGIS Outbound Declaration Generator",
    page_icon="📤",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# Error Handling Decorator
# ============================================================================

def handle_errors(func):
    """Decorator to handle errors gracefully for Regina"""
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            st.error(f"⚠️ Something went wrong. Please try again or contact support.")
            with st.expander("🔧 Technical Details (for IT support)"):
                st.code(str(e))
            return None
    return wrapper


# ============================================================================
# Dependency Check and Import
# ============================================================================

@st.cache_resource
def check_dependencies():
    """Check all dependencies are available"""
    missing = []
    try:
        from config.settings import Settings
    except ImportError as e:
        missing.append(f"config.settings: {e}")
    
    try:
        from pipeline import ProcessingPipeline, ProcessingProgress
    except ImportError as e:
        missing.append(f"pipeline: {e}")
    
    try:
        from models.shipment import (
            OutboundShipment, TransportMode, ValidationSeverity
        )
    except ImportError as e:
        missing.append(f"models.shipment: {e}")
    
    return missing

# Run dependency check
dep_errors = check_dependencies()
if dep_errors:
    st.error("⚠️ Application initialization failed. Missing dependencies:")
    for err in dep_errors:
        st.code(err)
    st.stop()

# Now import (dependencies verified)
from config.settings import Settings
from pipeline import ProcessingPipeline, ProcessingProgress
from models.shipment import (
    OutboundShipment, TransportMode, ValidationSeverity
)


# ============================================================================
# API Key Resolution (Supports Local & Deployed Environments)
# ============================================================================

def get_api_key_from_secrets() -> Optional[str]:
    """
    Resolve API key from multiple sources (priority order):
    1. Streamlit secrets (for deployed environment)
    2. Environment variable (for local development)
    3. None (will prompt user)
    """
    # Try Streamlit secrets first (deployed environment)
    try:
        if hasattr(st, 'secrets') and 'api' in st.secrets:
            key = st.secrets['api'].get('ANTHROPIC_API_KEY', '')
            if key and key.startswith('sk-ant-'):
                return key
    except Exception:
        pass
    
    # Try environment variable (local development)
    env_key = os.environ.get('ANTHROPIC_API_KEY', '')
    if env_key and env_key.startswith('sk-ant-'):
        return env_key
    
    return None


# ============================================================================
# Session State Initialization
# ============================================================================

def init_session_state():
    """Initialize session state variables"""
    if 'pipeline' not in st.session_state:
        st.session_state.pipeline = None
    if 'settings' not in st.session_state:
        st.session_state.settings = None
    if 'processed' not in st.session_state:
        st.session_state.processed = False
    if 'api_key_source' not in st.session_state:
        st.session_state.api_key_source = None
    
    # Try to load API key from secrets/env if not already set
    if 'api_key' not in st.session_state or not st.session_state.api_key:
        secret_key = get_api_key_from_secrets()
        if secret_key:
            st.session_state.api_key = secret_key
            st.session_state.api_key_source = "secrets"
            # Auto-initialize settings
            st.session_state.settings = Settings.load(api_key=secret_key)

init_session_state()


# ============================================================================
# Helper Functions
# ============================================================================

def get_pipeline() -> Optional[ProcessingPipeline]:
    """Get or create pipeline instance"""
    if st.session_state.pipeline is None:
        if st.session_state.settings is not None:
            st.session_state.pipeline = ProcessingPipeline(st.session_state.settings)
    return st.session_state.pipeline


def outbound_to_dataframe(shipments) -> pd.DataFrame:
    """Convert outbound shipment list to editable DataFrame"""
    records = []
    for s in shipments:
        # Check completeness
        is_complete = bool(s.date and s.flight_vehicle and s.destination)
        status = "✅" if is_complete else "⚠️"
        
        records.append({
            '⚡': status,
            'Invoice': s.invoice_number,
            'Date': s.date,
            'Flight/Vehicle': s.flight_vehicle,
            'Mode': s.mode.value if s.mode else '',
            'From': s.origin,
            'Destination': s.destination,
            'Description': s.description,
            'Currency': s.currency,
            'Value': s.value
        })
    return pd.DataFrame(records)


def dataframe_to_shipments(df: pd.DataFrame, original_shipments):
    """Update outbound shipments from edited DataFrame"""
    pipeline = get_pipeline()
    if not pipeline:
        return
    
    for idx, row in df.iterrows():
        if idx < len(original_shipments):
            updates = {
                'date': row.get('Date'),
                'flight_vehicle': row.get('Flight/Vehicle'),
                'destination': row.get('Destination'),
                'description': row.get('Description'),
                'currency': row.get('Currency'),
                'value': row.get('Value'),
            }
            pipeline.update_outbound_shipment(idx, updates)


# ============================================================================
# Sidebar
# ============================================================================

def render_sidebar():
    """Render sidebar configuration"""
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key Section
        api_key_source = st.session_state.get('api_key_source')
        
        if api_key_source == "secrets":
            st.success("🔐 API Key: Configured")
            st.caption("Loaded from application secrets")
        else:
            api_key = st.text_input(
                "Claude API Key",
                type="password",
                value=st.session_state.get('api_key', ''),
                help="Enter your Anthropic API key (starts with sk-ant-)"
            )
            
            if api_key and api_key != st.session_state.get('api_key', ''):
                if api_key.startswith('sk-ant-'):
                    st.session_state.api_key = api_key
                    st.session_state.api_key_source = "manual"
                    st.session_state.settings = Settings.load(api_key=api_key)
                    st.session_state.pipeline = None
                    st.success("✅ API Key saved")
                else:
                    st.error("⚠️ Invalid API key format")
        
        st.markdown("---")
        
        # Declaration Period
        declaration_period = st.text_input(
            "Declaration Period",
            value=st.session_state.get('declaration_period', 'October-25'),
            help="e.g., September-25, October-25"
        )
        st.session_state.declaration_period = declaration_period
        
        st.markdown("---")
        
        # Connection Status
        st.markdown("### 🔌 System Status")
        
        settings = st.session_state.settings
        if settings and settings.api.api_key:
            st.success("✅ Ready to process")
        else:
            st.warning("⚠️ API key required")
        
        st.markdown("---")
        
        # Info
        st.markdown("### ℹ️ Processing Info")
        st.info(
            f"**Rate Limit Delay:** 10 seconds between API calls\n\n"
            f"This ensures reliable processing without API errors."
        )
        
        # Stats
        pipeline = get_pipeline()
        if pipeline:
            result = pipeline.get_result()
            st.markdown("### 📊 Current Session")
            st.metric("Outbound Records", len(result.outbound_shipments))
        
        st.markdown("---")
        
        # Reset button
        if st.button("🔄 Reset Session", type="secondary", use_container_width=True):
            st.session_state.pipeline = None
            st.session_state.processed = False
            st.rerun()
        
        # Footer
        st.markdown("---")
        st.caption("v2.0 | Outbound Only | NeoAsia BA")


# ============================================================================
# Main Content - Upload Tab
# ============================================================================

def render_upload_tab():
    """Render the document upload tab - Outbound Only"""
    st.header("📤 Upload Outbound Documents")
    
    st.info("💡 Upload your Air Waybill (AWB) and Invoice PDFs for outbound shipments.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("✈️ Air Waybill PDFs")
        outbound_awb = st.file_uploader(
            "Upload Outbound AWB PDFs",
            type=['pdf'],
            accept_multiple_files=True,
            key="outbound_awb_upload",
            help="Air Waybills contain flight info and shipment dates"
        )
        
        if outbound_awb:
            st.success(f"✅ {len(outbound_awb)} AWB file(s) ready")
            for f in outbound_awb:
                st.caption(f"  📄 {f.name}")
    
    with col2:
        st.subheader("🧾 Invoice PDFs")
        outbound_inv = st.file_uploader(
            "Upload Outbound Invoice PDFs",
            type=['pdf'],
            accept_multiple_files=True,
            key="outbound_inv_upload",
            help="Commercial Invoices contain destination and value info"
        )
        
        if outbound_inv:
            st.success(f"✅ {len(outbound_inv)} Invoice file(s) ready")
            for f in outbound_inv:
                st.caption(f"  📄 {f.name}")
    
    # Store in session state
    st.session_state.outbound_awb = outbound_awb
    st.session_state.outbound_inv = outbound_inv
    
    # Summary
    total_files = len(outbound_awb or []) + len(outbound_inv or [])
    if total_files > 0:
        st.markdown("---")
        st.success(f"📁 **Total: {total_files} file(s) ready for processing**")
        st.caption("➡️ Go to the **Process** tab to extract data from these documents.")


# ============================================================================
# Main Content - Process Tab
# ============================================================================

def render_process_tab():
    """Render the processing tab - Outbound Only"""
    st.header("🔄 Process Outbound Documents")
    
    pipeline = get_pipeline()
    
    if not st.session_state.get('api_key'):
        st.error("⚠️ Please enter your Claude API key in the sidebar.")
        return
    
    if pipeline is None:
        st.session_state.settings = Settings.load(api_key=st.session_state.api_key)
        pipeline = ProcessingPipeline(st.session_state.settings)
        st.session_state.pipeline = pipeline
    
    # File summary
    awb_files = st.session_state.get('outbound_awb', [])
    inv_files = st.session_state.get('outbound_inv', [])
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("AWB Files", len(awb_files) if awb_files else 0)
    with col2:
        st.metric("Invoice Files", len(inv_files) if inv_files else 0)
    
    st.markdown("---")
    
    # Process button
    st.subheader("📄 Extract from Documents")
    
    if not (awb_files or inv_files):
        st.warning("⚠️ No files uploaded. Go to the Upload tab first.")
        return
    
    st.info(
        "🔍 **What will be extracted:**\n"
        "- From AWBs: Flight numbers, dates, AWB numbers\n"
        "- From Invoices: Destinations, values, currencies, descriptions"
    )
    
    if st.button("🚀 Process Outbound Documents", type="primary", use_container_width=True):
        temp_dir = tempfile.mkdtemp()
        
        awb_infos = []
        for f in awb_files or []:
            temp_path = os.path.join(temp_dir, f.name)
            with open(temp_path, 'wb') as tf:
                tf.write(f.read())
            awb_infos.append({'name': f.name, 'path': temp_path})
        
        inv_infos = []
        for f in inv_files or []:
            temp_path = os.path.join(temp_dir, f.name)
            with open(temp_path, 'wb') as tf:
                tf.write(f.read())
            inv_infos.append({'name': f.name, 'path': temp_path})
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        def update_progress(progress: ProcessingProgress):
            pct = progress.progress_percent / 100
            progress_bar.progress(pct)
            status_text.text(f"Processing: {progress.current_item}")
        
        with st.spinner("Extracting data from documents..."):
            shipments = pipeline.process_outbound_pdfs(awb_infos, inv_infos, update_progress)
        
        progress_bar.progress(1.0)
        status_text.empty()
        
        st.success(f"✅ **Processed {len(shipments)} outbound shipment(s)**")
        st.session_state.processed = True
        
        st.caption("➡️ Go to the **Review** tab to verify and edit extracted data.")


# ============================================================================
# Main Content - Review Tab
# ============================================================================

def render_review_tab():
    """Render the review and edit tab - Outbound Only"""
    st.header("✏️ Review & Edit Outbound Records")
    
    pipeline = get_pipeline()
    if not pipeline:
        st.info("No data to review. Process documents first.")
        return
    
    result = pipeline.get_result()
    
    if not result.outbound_shipments:
        st.info("No outbound records. Process outbound documents first.")
        return
    
    # Validation
    st.subheader("🔍 Validation")
    if st.button("Run Validation"):
        issues = pipeline.validate_all()
        
        # Filter to only outbound issues
        outbound_issues = {k: v for k, v in issues.items() if not k.startswith('PDO')}
        
        if not outbound_issues:
            st.success("✅ All outbound records passed validation")
        else:
            for ref, issue_list in outbound_issues.items():
                with st.expander(f"⚠️ {ref} - {len(issue_list)} issue(s)"):
                    for issue in issue_list:
                        icon = "🔴" if issue.severity == ValidationSeverity.ERROR else "🟡"
                        st.write(f"{icon} **{issue.field}:** {issue.message}")
                        if issue.suggestion:
                            st.caption(f"💡 {issue.suggestion}")
    
    st.markdown("---")
    
    # Completeness check
    incomplete = [s for s in result.outbound_shipments if not (s.date and s.flight_vehicle)]
    if incomplete:
        st.warning(
            f"⚠️ **{len(incomplete)} record(s) missing data:** "
            f"{', '.join(s.invoice_number for s in incomplete)}. "
            f"Check Date and Flight/Vehicle fields below."
        )
    
    # Data Editor
    st.subheader("📝 Edit Records")
    st.caption("⚡ Status: ✅ = Complete | ⚠️ = Missing fields (needs review)")
    
    df_outbound = outbound_to_dataframe(result.outbound_shipments)
    
    edited_outbound = st.data_editor(
        df_outbound,
        num_rows="dynamic",
        use_container_width=True,
        key="outbound_editor",
        disabled=['⚡'],  # Status column is read-only
        column_config={
            'Date': st.column_config.DateColumn('Date', format='YYYY-MM-DD'),
            'Value': st.column_config.NumberColumn('Value', format='%.2f'),
        }
    )
    
    if st.button("💾 Save Changes", type="primary"):
        dataframe_to_shipments(edited_outbound, result.outbound_shipments)
        st.success("✅ Changes saved!")
        st.rerun()


# ============================================================================
# Main Content - Export Tab
# ============================================================================

def render_export_tab():
    """Render the export tab - Outbound Only"""
    st.header("📊 Generate Declaration")
    
    pipeline = get_pipeline()
    if not pipeline:
        st.warning("No data to export. Process documents first.")
        return
    
    result = pipeline.get_result()
    declaration_period = st.session_state.get('declaration_period', 'October-25')
    
    if not result.outbound_shipments:
        st.warning("No outbound records to export. Process documents first.")
        return
    
    # Summary
    st.subheader("📋 Export Summary")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Outbound Records", len(result.outbound_shipments))
    with col2:
        # Calculate total value by currency
        currencies = {}
        for s in result.outbound_shipments:
            curr = s.currency or 'USD'
            currencies[curr] = currencies.get(curr, 0) + (s.value or 0)
        st.metric("Currencies", len(currencies))
    with col3:
        st.metric("Processing Time", f"{result.processing_time_seconds:.1f}s")
    
    st.markdown(f"**Declaration Period:** {declaration_period}")
    
    # Currency breakdown
    if currencies:
        st.markdown("**Value by Currency:**")
        for curr, total in sorted(currencies.items()):
            st.write(f"  • **{curr}:** {total:,.2f}")
    
    st.markdown("---")
    
    # Generate button
    if st.button("🚀 Generate Excel File", type="primary", use_container_width=True):
        
        with st.spinner("Generating Excel file..."):
            excel_bytes = pipeline.generate_outbound_excel(declaration_period)
        
        st.success("✅ Excel file generated!")
        
        filename = f"Marine_Ins_Declare_OUT_{declaration_period.replace('-', '_')}.xlsx"
        
        st.download_button(
            label="📥 Download Outbound Declaration Excel",
            data=excel_bytes,
            file_name=filename,
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            type="primary",
            use_container_width=True
        )
    
    st.markdown("---")
    
    # Audit trail
    st.subheader("📋 Audit Trail")
    
    if st.checkbox("Show Audit Trail"):
        audit_df = pipeline.get_audit_trail()
        if not audit_df.empty:
            st.dataframe(audit_df, use_container_width=True)
            
            csv = audit_df.to_csv(index=False)
            st.download_button(
                "Download Audit Log (CSV)",
                csv,
                "audit_trail.csv",
                "text/csv"
            )
        else:
            st.info("No audit entries yet")


# ============================================================================
# Main App
# ============================================================================

def main():
    st.title("📤 MGIS Outbound Declaration Generator")
    st.markdown("**NeoAsia (S) Pte Ltd** - Business Analytics Team")
    st.markdown("---")
    
    # Sidebar
    render_sidebar()
    
    # Check if API key is configured
    settings = st.session_state.settings
    if not settings or not settings.api.api_key:
        st.warning("⚠️ **API Key Required**")
        st.info(
            "Please enter your Claude API key in the sidebar to begin processing.\n\n"
            "Need an API key? Contact Abhiraj or visit [Anthropic Console](https://console.anthropic.com)"
        )
        
        # Show welcome message with instructions
        with st.expander("📖 How to Use This Application", expanded=True):
            st.markdown("""
            ### Quick Start Guide
            
            1. **Configure API Key** (sidebar) - Enter your Claude API key
            2. **Upload Documents** (Upload tab)
               - Outbound AWB PDFs
               - Outbound Invoice PDFs
            3. **Process Documents** (Process tab) - Click process button
            4. **Review & Edit** (Review tab) - Verify extracted data
            5. **Generate Excel** (Export tab) - Download declaration file
            
            ### Document Types Supported
            - Air Waybills (AWB) - for flight info and dates
            - Commercial Invoices - for destinations and values
            """)
        return
    
    # Main tabs (simplified for outbound only)
    tab1, tab2, tab3, tab4 = st.tabs([
        "📤 Upload",
        "🔄 Process", 
        "✏️ Review",
        "📊 Export"
    ])
    
    with tab1:
        render_upload_tab()
    
    with tab2:
        render_process_tab()
    
    with tab3:
        render_review_tab()
    
    with tab4:
        render_export_tab()


if __name__ == "__main__":
    main()
