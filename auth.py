import streamlit as st
from typing import Any, Dict
from services.firebase import get_pyrebase_auth, get_firestore_client
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
    auth = get_pyrebase_auth()
    tab_login, tab_register = st.tabs(["Giriş Yap", "Kayıt Ol"]) 

    with tab_register:
        st.subheader("Yeni Hesap Oluştur")
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("Ad")
            last_name = st.text_input("Soyad")
            age = st.number_input("Yaş", min_value=0, max_value=120, value=25)
            gender = st.selectbox("Cinsiyet", ["Erkek", "Kadın", "Diğer"]) 
            education = st.selectbox(
                "Eğitim Durumu",
                ["İlkokul", "Ortaokul", "Lise", "Ön Lisans", "Lisans", "Yüksek Lisans", "Doktora", "Diğer"],
            )
        with col2:
            med_options = [
                "Hipertansiyon", "Diyabet", "Depresyon", "Anksiyete", "Epilepsi", "Migren",
                "Uyku Bozuklukları", "Kardiyovasküler Hastalık", "Tiroid Hastalıkları", "Nörolojik Bozukluklar",
            ]
            medical_sel = st.multiselect("Kişisel Hastalıklar", med_options)
            medical_other = st.text_input("Diğer (kişisel)")
            family_sel = st.multiselect("Ailede Görülen Hastalıklar", med_options)
            family_other = st.text_input("Diğer (aile)")
            email_r = st.text_input("Email")
            password_r = st.text_input("Şifre", type="password")

        if st.button("Kayıt Ol", type="primary"):
            try:
                if not email_r or not password_r:
                    st.error("Email ve şifre zorunludur.")
                else:
                    user = auth.create_user_with_email_and_password(email_r, password_r)
                    uid = user.get("localId") or user.get("uid")
                    medical = ", ".join([*medical_sel, *( [medical_other] if medical_other else [] )])
                    family = ", ".join([*family_sel, *( [family_other] if family_other else [] )])
                    profile = {
                        "firstName": first_name,
                        "lastName": last_name,
                        "age": int(age),
                        "gender": gender,
                        "educationLevel": education,
                        "medicalConditions": medical,
                        "familyMedicalHistory": family,
                    }
                    _upsert_user_profile(uid, email_r, profile)
                    _set_session_user(uid, email_r, profile)
                    st.success("Kayıt başarılı. Yönlendiriliyorsunuz…")
                    st.rerun()
            except Exception as e:
                msg = str(e)
                if "EMAIL_EXISTS" in msg:
                    st.error("Bu email ile bir hesap zaten mevcut. Lütfen giriş yapın veya şifre sıfırlayın.")
                else:
                    st.error(f"Kayıt başarısız: {e}")

    with tab_login:
        st.subheader("Hesabınıza Giriş Yapın")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Şifre", type="password", key="login_password")
        colA, colB = st.columns([1,1])
        with colA:
            if st.button("Giriş Yap", type="primary"):
                try:
                    user = auth.sign_in_with_email_and_password(email, password)
                    uid = user.get("localId") or user.get("uid")
                    db = get_firestore_client()
                    doc = db.collection("users").document(uid).get()
                    profile = {}
                    if doc.exists:
                        data = doc.to_dict()
                        profile = data.get("profile", {})
                    else:
                        profile = {"firstName": "", "lastName": ""}
                    _update_last_login(uid)
                    _set_session_user(uid, email, profile)
                    st.success("Giriş başarılı. Yönlendiriliyorsunuz…")
                    st.rerun()
                except Exception as e:
                    msg = str(e)
                    if "EMAIL_NOT_FOUND" in msg or "INVALID_LOGIN_CREDENTIALS" in msg:
                        st.error("Email veya şifre hatalı.")
                    else:
                        st.error(f"Giriş başarısız: {e}")
        with colB:
            if st.button("Şifre Sıfırlama Linki Gönder"):
                try:
                    if not email:
                        st.warning("Lütfen email girin.")
                    else:
                        auth.send_password_reset_email(email)
                        st.success("Sıfırlama e-postası gönderildi.")
                except Exception as e:
                    st.error(f"Sıfırlama hatası: {e}")