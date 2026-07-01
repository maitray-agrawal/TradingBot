"""Reports Page for the PrimeTrade AI dashboard."""

import os
from pathlib import Path
import streamlit as st

from dashboard.components import hero_banner
from analytics.analysis.analytics_engine import AnalyticsEngine
from analytics.statistics.statistics_engine import StatisticsEngine
from analytics.reports.report_engine import ReportingEngine

hero_banner(
    title="📋 Report Compilation Desk",
    subtitle="Generate publication-quality Executive, Technical, and Business reports in HTML and PDF formats.",
)

active_path = Path(st.session_state.active_dataset_path) if st.session_state.active_dataset_path else None

if not active_path or not active_path.exists():
    st.warning("⚠️ No active dataset has been selected. Please upload a dataset first in the **Upload Dataset** page.")
else:
    st.info(
        "📝 **Click below to generate all reports**: This compiles the raw trading data and "
        "statistical tests into styled documents saved in the reports directory."
    )
    
    if st.button("⚡ Compile Reports (PDF, HTML, MD)"):
        with st.spinner("Generating performance summaries and drafting PDFs..."):
            try:
                # 1. Load data
                import pandas as pd
                df = pd.read_csv(active_path)
                
                # 2. Run analysis
                analytics_res = AnalyticsEngine.run_analysis(df, export_outputs=False)
                statistics_res = StatisticsEngine.run_statistics(df, export_outputs=False)
                
                # 3. Compile reports
                engine = ReportingEngine()
                report_paths = engine.run_reporting(analytics_res, statistics_res)
                
                # Store paths in session state
                st.session_state.compiled_reports = report_paths
                st.success("✅ Reports compiled successfully!")
                
            except Exception as e:
                st.error(f"❌ Failed to compile reports: {e}")
                
    # Display download triggers if reports exist
    if "compiled_reports" in st.session_state and st.session_state.compiled_reports:
        reports = st.session_state.compiled_reports
        
        st.markdown("### 📥 Download Compiled Reports")
        
        for name, formats in reports.items():
            st.markdown(f"#### 📄 {name.replace('_', ' ').title()}")
            col1, col2, col3 = st.columns(3)
            
            # PDF Format
            if "pdf" in formats and Path(formats["pdf"]).exists():
                pdf_path = Path(formats["pdf"])
                with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
                with col1:
                    st.download_button(
                        label="Download PDF Report",
                        data=pdf_bytes,
                        file_name=pdf_path.name,
                        mime="application/pdf",
                        use_container_width=True,
                    )
                    
            # HTML Format
            if "html" in formats and Path(formats["html"]).exists():
                html_path = Path(formats["html"])
                with open(html_path, "r", encoding="utf-8") as f:
                    html_content = f.read()
                with col2:
                    st.download_button(
                        label="Download HTML Report",
                        data=html_content,
                        file_name=html_path.name,
                        mime="text/html",
                        use_container_width=True,
                    )
                    
            # MD Format
            if "md" in formats and Path(formats["md"]).exists():
                md_path = Path(formats["md"])
                with open(md_path, "r", encoding="utf-8") as f:
                    md_content = f.read()
                with col3:
                    st.download_button(
                        label="Download Markdown Report",
                        data=md_content,
                        file_name=md_path.name,
                        mime="text/plain",
                        use_container_width=True,
                    )
                    
            # Expander for a quick in-app Markdown preview
            if "md" in formats and Path(formats["md"]).exists():
                with st.expander(f"👁️ Preview {name.replace('_', ' ').title()}"):
                    st.markdown(md_content)
    else:
        # Check if they are already on disk
        reports_dir = Path("analytics/reports/generated")
        if reports_dir.exists():
            pdf_files = list(reports_dir.glob("*.pdf"))
            if pdf_files:
                st.subheader("📁 Pre-existing Generated Reports found:")
                for pdf_f in pdf_files:
                    base_name = pdf_f.stem
                    st.markdown(f"**{base_name.replace('_', ' ').title()}**")
                    col1, col2 = st.columns(2)
                    
                    with open(pdf_f, "rb") as f:
                        pdf_bytes = f.read()
                    with col1:
                        st.download_button(
                            label=f"Download {pdf_f.name}",
                            data=pdf_bytes,
                            file_name=pdf_f.name,
                            mime="application/pdf",
                            key=f"pre_pdf_{base_name}",
                        )
                        
                    html_f = reports_dir / f"{base_name}.html"
                    if html_f.exists():
                        with open(html_f, "r", encoding="utf-8") as f:
                            html_content = f.read()
                        with col2:
                            st.download_button(
                                label=f"Download {html_f.name}",
                                data=html_content,
                                file_name=html_f.name,
                                mime="text/html",
                                key=f"pre_html_{base_name}",
                            )
