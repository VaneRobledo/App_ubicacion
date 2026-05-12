import streamlit as st
from pathlib import Path

CSS_PATH = Path(__file__).resolve().parent / "assets" / "styles.css"

def load_local_css():
    if CSS_PATH.exists():
        with open(CSS_PATH, "r", encoding="utf-8", errors="ignore") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    else:
        st.warning("No se encontró el archivo CSS local: assets/styles.css")


def get_svg_icon(name, color="#708238", size=24):
    """Genera el código SVG para diferentes iconos."""
    icons = {
        "pin": f'<path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle>',
        "search": '<circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line>',
        "insight": f'<path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A5 5 0 0 0 8 8c0 1.3.5 2.6 1.5 3.5.8.8 1.3 1.5 1.5 2.5"></path><line x1="9" y1="18" x2="15" y2="18"></line><line x1="10" y1="22" x2="14" y2="22"></line>',
        "check": '<polyline points="20 6 9 17 4 12"></polyline>',
        "info": '<circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line>',
        "alert": '<path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line>'
    }
    return f"""<svg width=\"{size}\" height=\"{size}\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"{color}\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" style=\"display:inline-block; vertical-align:middle; margin-right:8px;\">{icons.get(name, icons['pin'])}</svg>"""


def st_custom_header(text, icon="pin", color="#708238", level="h1"):
    """Renderiza encabezados con iconos SVG."""
    st.markdown(
        f'<{level} style="color: #4a4a4a; display: flex; align-items: center;">{get_svg_icon(icon, color, size=35 if level=="h1" else 28 if level=="h2" else 24)}{text}</{level}>',
        unsafe_allow_html=True
    )


def st_custom_message(text, type="info"):
    """Renderiza mensajes personalizados con estilo cálido."""
    config = {
        "info": {"color": "#708238", "bg": "rgba(112, 130, 56, 0.1)", "icon": "info"},
        "warning": {"color": "#c39953", "bg": "rgba(195, 153, 83, 0.1)", "icon": "alert"},
        "success": {"color": "#708238", "bg": "rgba(112, 130, 56, 0.15)", "icon": "check"}
    }
    c = config.get(type, config["info"])
    st.markdown(
        f"""
        <div class="custom-message" style="border-left-color: {c['color']}; background-color: {c['bg']}; color: #4a4a4a;">
            {get_svg_icon(c['icon'], c['color'], size=20)} {text}
        </div>
        """,
        unsafe_allow_html=True
    )
