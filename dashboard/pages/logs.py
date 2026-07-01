"""Logs Viewer Page for the PrimeTrade AI dashboard."""

from pathlib import Path
import streamlit as st

from dashboard.components import hero_banner

hero_banner(
    title="📜 System Logs & Activity Viewer",
    subtitle="Tail and filter execution messages from analytics, system, and error logging targets.",
)

logs_dir = Path("logs")
if not logs_dir.exists() or not logs_dir.is_dir():
    st.info("No log files discovered in this environment. Wait for processes to run.")
else:
    # Get all log files
    log_files = sorted(list(logs_dir.glob("*.log")))
    
    if not log_files:
        st.info("No log files discovered in this environment. Wait for processes to run.")
    else:
        file_names = [f.name for f in log_files]
        
        st.markdown("### 🔍 Select and Filter Log Activity")
        col_file, col_tail = st.columns([2, 1])
        
        with col_file:
            selected_file_name = st.selectbox("Select Log Target File", options=file_names, index=0)
            
        with col_tail:
            tail_lines = st.slider("Tail Lines (View last N lines)", min_value=10, max_value=500, value=100, step=10)
            
        search_query = st.text_input("Search Keyword / Text Filter (Case-Insensitive)", "")
        
        if st.button("🔄 Refresh Logs"):
            st.rerun()
            
        # Read the file
        selected_file_path = logs_dir / selected_file_name
        
        if selected_file_path.exists():
            try:
                with open(selected_file_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                
                # Slice to tail count
                tail_sliced = lines[-tail_lines:] if len(lines) > tail_lines else lines
                
                # Apply filter
                if search_query:
                    q = search_query.lower()
                    filtered_lines = [line for line in tail_sliced if q in line.lower()]
                else:
                    filtered_lines = tail_sliced
                    
                # Format for presentation
                log_text = "".join(filtered_lines)
                
                if log_text:
                    st.markdown(
                        f"""
                        <div class="terminal-box">
{log_text}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                else:
                    st.info("No log entries match the search filter.")
                    
            except Exception as e:
                st.error(f"Failed to read log file: {e}")
        else:
            st.error(f"Selected log file path does not exist: `{selected_file_path}`")
