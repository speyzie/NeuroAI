import streamlit as st

from auth import render_auth_page
from dashboard import render_dashboard_page
from tests import render_tests_page
from results import render_results_page
from reports import render_reports_page
from settings import render_settings_page


def ensure_session_defaults() -> None:
    if "is_authenticated" not in st.session_state:
        st.session_state.is_authenticated = False
    if "user" not in st.session_state:
        st.session_state.user = None
    if "active_page" not in st.session_state:
        st.session_state.active_page = "Ana Sayfa"


def render_sidebar() -> None:
    with st.sidebar:
        # Custom CSS for dark theme
        st.markdown("""
        <style>
        .sidebar .sidebar-content {
            background-color: #1e1e1e;
        }
        .css-1d391kg {
            background-color: #1e1e1e;
        }
        .css-1lcbmhc {
            background-color: #1e1e1e;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Top section with brain icon and welcome
        st.markdown("""
        <div style='text-align: center; padding: 20px 0;'>
            <h1 style='color: #ff69b4; font-size: 24px; margin: 0;'>🧠</h1>
            <h2 style='color: white; font-size: 20px; margin: 10px 0;'>NeuroAI</h2>
        </div>
        """, unsafe_allow_html=True)
        
        if st.session_state.is_authenticated and st.session_state.user:
            user_profile = st.session_state.user.get("profile", {})
            user_name = f"{user_profile.get('firstName', '')} {user_profile.get('lastName', '')}".strip()
            if not user_name:
                user_name = "Kullanıcı"
            
            st.markdown(f"""
            <div style='text-align: center; padding: 10px 0;'>
                <p style='color: #cccccc; font-size: 14px; margin: 0;'>Hoş geldiniz, {user_name}!</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.divider()
            
            # Profile Information
            st.markdown("""
            <div style='margin: 20px 0;'>
                <h3 style='color: white; font-size: 16px; margin: 10px 0;'>👤 Profil Bilgileri</h3>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style='color: #cccccc; font-size: 14px; margin: 5px 0;'>
                Yaş: {user_profile.get('age', 'N/A')}
            </div>
            <div style='color: #cccccc; font-size: 14px; margin: 5px 0;'>
                Cinsiyet: {user_profile.get('gender', 'N/A')}
            </div>
            <div style='color: #cccccc; font-size: 14px; margin: 5px 0;'>
                Eğitim: {user_profile.get('educationLevel', 'N/A')}
            </div>
            """, unsafe_allow_html=True)
            
            st.divider()
            
            # Navigation
            st.markdown("""
            <div style='margin: 20px 0;'>
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
    # Set page config with dark theme
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