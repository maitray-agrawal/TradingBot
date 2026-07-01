"""Custom CSS styles and UI component injections for the PrimeTrade AI dashboard."""

import streamlit as st


def inject_custom_styles() -> None:
    """Injects premium, state-of-the-art CSS styling into the Streamlit page."""
    css_content = """
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;700;800&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    
    <style>
    /* Global Font Overrides */
    html, body, [class*="css"], .stApp {
        font-family: 'Inter', sans-serif !important;
    }
    
    h1, h2, h3, h4, h5, h6, .main-title {
        font-family: 'Outfit', sans-serif !important;
        font-weight: 700;
    }
    
    /* Elegant Dark Glassmorphic card container */
    .glass-card {
        background: rgba(25, 30, 40, 0.65) !important;
        backdrop-filter: blur(10px) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 12px !important;
        padding: 20px !important;
        margin-bottom: 20px !important;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.3) !important;
        transition: transform 0.2s ease, border-color 0.2s ease !important;
    }
    
    .glass-card:hover {
        transform: translateY(-2px);
        border-color: rgba(0, 191, 255, 0.3) !important;
    }
    
    /* Gradient Banners */
    .hero-banner {
        background: linear-gradient(135deg, #1f4068 0%, #162447 50%, #0f1a1c 100%) !important;
        border-radius: 12px;
        padding: 30px;
        margin-bottom: 25px;
        border-left: 5px solid #00bfff;
        box-shadow: 0 4px 20px rgba(0, 191, 255, 0.15);
    }
    
    .hero-title {
        color: #ffffff !important;
        margin: 0 !important;
        font-size: 2.2rem !important;
        font-weight: 800 !important;
        letter-spacing: -0.5px;
    }
    
    .hero-subtitle {
        color: #a0aec0 !important;
        margin-top: 5px !important;
        font-size: 1.1rem !important;
        font-weight: 400 !important;
    }
    
    /* Styled Badges */
    .badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-right: 5px;
    }
    
    .badge-success {
        background-color: rgba(72, 187, 120, 0.2) !important;
        color: #48bb78 !important;
        border: 1px solid rgba(72, 187, 120, 0.4) !important;
    }
    
    .badge-warning {
        background-color: rgba(236, 151, 31, 0.2) !important;
        color: #ec971f !important;
        border: 1px solid rgba(236, 151, 31, 0.4) !important;
    }
    
    .badge-danger {
        background-color: rgba(229, 62, 62, 0.2) !important;
        color: #e53e3e !important;
        border: 1px solid rgba(229, 62, 62, 0.4) !important;
    }
    
    .badge-info {
        background-color: rgba(0, 191, 255, 0.2) !important;
        color: #00bfff !important;
        border: 1px solid rgba(0, 191, 255, 0.4) !important;
    }
    
    /* Custom Styled Table Headers */
    .stTable th {
        background-color: rgba(30, 41, 59, 0.8) !important;
        color: #e2e8f0 !important;
        font-weight: 600 !important;
    }
    
    /* Premium Sidebar Styling */
    .css-1d391kg {
        background-color: #0f172a !important;
    }
    
    /* Metric styling */
    div[data-testid="stMetricValue"] {
        font-family: 'Outfit', sans-serif !important;
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #f8fafc !important;
    }
    
    div[data-testid="stMetricLabel"] {
        color: #94a3b8 !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    
    /* Custom terminal box for logs */
    .terminal-box {
        font-family: 'Courier New', Courier, monospace !important;
        background-color: #0d1117 !important;
        color: #c9d1d9 !important;
        border-radius: 6px;
        padding: 15px;
        font-size: 0.85rem;
        line-height: 1.4;
        border: 1px solid #30363d;
        overflow-x: auto;
        white-space: pre-wrap;
        max-height: 400px;
    }
    </style>
    """
    st.markdown(css_content, unsafe_allow_html=True)


def glass_card(title: str, content: str, subtitle: str = "") -> None:
    """Renders a beautiful glassmorphic container with custom titles and content."""
    sub_html = f"<div style='color:#a0aec0;font-size:0.85rem;margin-top:5px;'>{subtitle}</div>" if subtitle else ""
    st.markdown(
        f"""
        <div class="glass-card">
            <h3 style="margin-top:0;color:#00bfff;font-size:1.25rem;">{title}</h3>
            <div style="font-size:1.1rem;color:#f7fafc;line-height:1.5;">{content}</div>
            {sub_html}
        </div>
        """,
        unsafe_allow_html=True,
    )


def hero_banner(title: str, subtitle: str) -> None:
    """Renders a premium visual welcome banner."""
    st.markdown(
        f"""
        <div class="hero-banner">
            <div class="hero-title">{title}</div>
            <div class="hero-subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
