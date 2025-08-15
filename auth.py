import streamlit as st
from typing import Any, Dict
from services.firebase import get_firebase_auth, get_firestore_client
from google.cloud import firestore as gfs
import datetime as dt


def _set_session_user(uid: str, email: str, profile: Dict[str, Any]) -> None:
    st.session_state.is_authenticated = True
    st.session_state.user = {
        "uid": uid,
        "email": email,
        "profile": profile,
    }
    st.session_state.active_page = "Dashboard"


def _upsert_user_profile(uid: str, email: str, profile: Dict[str, Any]) -> None:
    db = get_firestore_client()
    user_ref = db.collection("users").document(uid)
    base = {
        "profile": {
            "firstName": profile.get("firstName", ""),
            "lastName": profile.get("lastName", ""),
            "email": email,
            "age": profile.get("age", 0),
            "gender": profile.get("gender", "Diğer"),
            "educationLevel": profile.get("educationLevel", "Diğer"),
            "medicalConditions": profile.get("medicalConditions", ""),
            "familyMedicalHistory": profile.get("familyMedicalHistory", ""),
            "createdAt": gfs.SERVER_TIMESTAMP,
            "lastLogin": gfs.SERVER_TIMESTAMP,
        },
        "preferences": {
            "theme": profile.get("theme", "light"),
            "notifications": bool(profile.get("notifications", True)),
            "dataSharing": bool(profile.get("dataSharing", False)),
        },
    }
    user_ref.set(base, merge=True)


def _update_last_login(uid: str) -> None:
    db = get_firestore_client()
    user_ref = db.collection("users").document(uid)
    user_ref.set({"profile": {"lastLogin": gfs.SERVER_TIMESTAMP}}, merge=True)


def render_auth_page() -> None:
    st.title("🧠 NeuroAI | Giriş / Kayıt")
    auth = get_firebase_auth()
    
    # For demo purposes, we'll use a simple form-based authentication
    st.subheader("Demo Giriş")
    
    email = st.text_input("Email")
    password = st.text_input("Şifre", type="password")
    
    if st.button("Giriş Yap", type="primary"):
        if email and password:
            # For demo, accept any email/password
            profile = {
                "firstName": "Demo",
                "lastName": "Kullanıcı",
                "age": 25,
                "gender": "Diğer",
                "educationLevel": "Lisans",
                "medicalConditions": "",
                "familyMedicalHistory": "",
            }
            _set_session_user("demo_user", email, profile)
            st.success("Giriş başarılı. Yönlendiriliyorsunuz…")
            st.rerun()
        else:
            st.error("Email ve şifre zorunludur.")
    
    st.divider()
    st.info("Demo için herhangi bir email ve şifre ile giriş yapabilirsiniz.")