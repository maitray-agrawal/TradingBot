"""Upload Dataset Page for the PrimeTrade AI dashboard."""

import os
from pathlib import Path
import streamlit as st
import pandas as pd

from config import settings
from analytics.ingestion import IngestionEngine
from analytics.ingestion.dataset_registry import DatasetRegistry
from dashboard.components import hero_banner

hero_banner(
    title="📤 Dataset Ingestion Center",
    subtitle="Upload raw trader records or Fear & Greed sentiment files to integrate into the pipeline.",
)

# Active registry
registry = DatasetRegistry()
engine = IngestionEngine()

st.subheader("📁 Upload New File")
uploaded_file = st.file_uploader(
    "Choose a file (CSV, Excel, JSON, Parquet)",
    type=["csv", "xlsx", "xls", "json", "parquet"],
)

if uploaded_file is not None:
    # Build uploads directory
    uploads_dir = Path(settings.data_directory) / "uploads"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    
    target_path = uploads_dir / uploaded_file.name
    
    # Save file contents
    with open(target_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
        
    st.success(f"💾 File successfully saved to: `{target_path.relative_to(Path(os.getcwd()))}`")
    
    # Run ingestion engine
    with st.spinner("Ingesting and validating dataset schema..."):
        try:
            dataset = engine.load_dataset(str(target_path))
            
            # Select as active dataset globally
            st.session_state.active_dataset_name = uploaded_file.name
            st.session_state.active_dataset_path = str(target_path)
            
            st.markdown("---")
            st.subheader("📊 Ingestion Diagnostics Results")
            
            # Displays quality score
            qual = dataset.quality_report
            score_color = "green" if qual.quality_score > 85.0 else ("orange" if qual.quality_score > 60.0 else "red")
            st.markdown(
                f"""
                <div style="background-color:rgba(30,41,59,0.5); padding:15px; border-radius:10px; border-left: 5px solid {score_color}; margin-bottom:20px;">
                    <h4 style="margin-top:0;">Dataset Type: <b>{dataset.dataset_type.name}</b></h4>
                    <p style="font-size:1.1rem;">Quality Score: <b style="color:{score_color};">{qual.quality_score:.1f}/100.0</b></p>
                    <p><b>Issues Discovered:</b> {len(qual.potential_issues)}</p>
                    <p><b>Recommendations:</b></p>
                    <ul>
                        {"".join(f"<li>{r}</li>" for r in qual.recommendations)}
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )
            
            # Mappings & columns
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### Column Mapping")
                st.dataframe(
                    pd.DataFrame(
                        list(dataset.column_mapping.items()),
                        columns=["Original Header", "Normalized Target"],
                    ),
                    use_container_width=True,
                )
            
            with col2:
                st.markdown("#### File Metadata")
                meta = dataset.metadata
                st.markdown(
                    f"""
                    - **Total Rows**: {meta.rows}
                    - **Total Columns**: {meta.columns}
                    - **Size on Disk**: {meta.file_size_bytes} bytes
                    - **Checksum**: `{meta.file_checksum[:30]}...`
                    - **Ingestion Time**: {meta.load_time_seconds:.4f}s
                    """
                )
                
            st.markdown("#### Data Preview (First 3 Rows)")
            st.dataframe(dataset.dataframe.head(3), use_container_width=True)
            
            st.info("💡 **Active Selection Updated**: This file has been selected as the current analysis model.")
            
        except Exception as e:
            st.error(f"❌ Failed to ingest dataset: {e}")
            if target_path.exists():
                os.remove(target_path)

# Show Registered Datasets List
st.markdown("---")
st.subheader("📚 Currently Registered Datasets")
registered = registry.list_datasets()
if registered:
    registered_df = []
    for data in registered:
        registered_df.append({
            "Filename": data.get("name"),
            "Dataset Type": data.get("dataset_type", "UNKNOWN"),
            "Row Count": data.get("rows", 0),
            "Size (Bytes)": data.get("file_size_bytes", 0),
            "Last Modified": data.get("last_modified", ""),
        })
    st.dataframe(pd.DataFrame(registered_df), use_container_width=True)
else:
    st.info("No datasets registered yet. Please upload a file above.")
