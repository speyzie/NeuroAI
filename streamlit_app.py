import streamlit as st
import time
import random
import pandas as pd
import altair as alt
from datetime import datetime as dt
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
import io
import base64

# Import our modules
from services.firebase import get_firestore_client, get_pyrebase_auth
from auth import render_auth_page
from dashboard import render_dashboard_page
from tests import render_tests_page
from results import render_results_page
from reports import render_reports_page
from settings import render_settings_page

# Set page config
st.set_page_config(
    page_title="NeuroAI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for dark theme
st.markdown("""
<style>
.main .block-container {
    background-color: #0e1117;
    color: white;
}
.stApp {
    background-color: #0e1117;
}
.css-1d391kg {
    background-color: #0e1117;
}
.css-1lcbmhc {
    background-color: #0e1117;
}
h1, h2, h3 {
    color: white !important;
}
.stButton > button {
    background-color: #ff69b4;
    color: white;
    border: none;
    border-radius: 5px;
    padding: 10px 20px;
}
.stButton > button:hover {
    background-color: #ff1493;
}
</style>
""", unsafe_allow_html=True)

def ensure_session_defaults() -> None:
    """Ensure all session state variables have default values"""
    defaults = {
        "is_authenticated": False,
        "user": None,
        "active_page": "Ana Sayfa",
    }
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

def render_sidebar() -> None:
    """Render the sidebar with navigation and user info"""
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; padding: 20px 0;'>
            <h2 style='color: #ff69b4; margin: 0;'>🧠 NeuroAI</h2>
            <p style='color: #cccccc; font-size: 14px; margin: 5px 0;'>Bilişsel Değerlendirme Platformu</p>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.is_authenticated and st.session_state.user:
            user = st.session_state.user
            st.markdown("""
            <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 20px 0;'>
                <h3 style='color: white; font-size: 16px; margin: 10px 0;'>👤 Profil Bilgileri</h3>
            </div>
            """, unsafe_allow_html=True)
            
            # User profile info
            if user.get("profile"):
                profile = user["profile"]
                st.markdown(f"**Yaş:** {profile.get('age', 'Belirtilmemiş')}")
                st.markdown(f"**Cinsiyet:** {profile.get('gender', 'Belirtilmemiş')}")
                st.markdown(f"**Eğitim:** {profile.get('education', 'Belirtilmemiş')}")
            
            st.markdown(f"""
            <div style='text-align: center; padding: 10px 0;'>
                <p style='color: #ff69b4; font-size: 16px; margin: 0;'>Hoş geldiniz, {user.get('displayName', 'Kullanıcı')}!</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div style='background-color: #1e1e1e; padding: 15px; border-radius: 10px; margin: 20px 0;'>
                <h3 style='color: white; font-size: 16px; margin: 10px 0;'>🧭 Navigasyon</h3>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("**Sayfa Seçin:**")
            
            nav_options = [
                ("🏠 Ana Sayfa", "Ana Sayfa"),
                ("🧠 Bilişsel Testler", "Bilişsel Testler"),
                ("📊 Sonuçlar", "Sonuçlar"),
                ("📋 Raporlar", "Raporlar"),
                ("⚙️ Ayarlar", "Ayarlar"),
            ]
            
            nav = st.selectbox(
                "Sayfa Seçin",
                options=[opt[1] for opt in nav_options],
                index=0,
                label_visibility="collapsed"
            )
            
            # Update active page
            if nav != st.session_state.active_page:
                st.session_state.active_page = nav
                st.rerun()
        else:
            # Show only login message
            st.markdown("""
            <div style='text-align: center; padding: 20px 0;'>
                <p style='color: #cccccc; font-size: 16px; margin: 0;'>Giriş yapmak için sağ taraftaki formu kullanın</p>
            </div>
            """, unsafe_allow_html=True)

PAGE_RENDERERS = {
    "Ana Sayfa": render_dashboard_page,
    "Bilişsel Testler": render_tests_page,
    "Sonuçlar": render_results_page,
    "Raporlar": render_reports_page,
    "Ayarlar": render_settings_page,
    "Auth": render_auth_page,
}

def main() -> None:
    ensure_session_defaults()
    render_sidebar()

    active = st.session_state.active_page
    if active != "Auth" and not st.session_state.is_authenticated:
        st.warning("Lütfen giriş yapın")
        render_auth_page()
        return

    renderer = PAGE_RENDERERS.get(active, render_dashboard_page)
    renderer()

if __name__ == "__main__":
    main() 