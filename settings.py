import streamlit as st
from typing import Any, Dict
from services.firebase import get_firestore_client


def _load_profile(uid: str) -> Dict[str, Any]:
    db = get_firestore_client()
    doc = db.collection("users").document(uid).get()
    return doc.to_dict() or {}


def render_settings_page() -> None:
    st.title("⚙️ Settings")
    uid = st.session_state.user.get("uid") if st.session_state.user else None
    if not uid:
        st.warning("Giriş gerekli")
        return

    data = _load_profile(uid)
    profile = data.get("profile", {})
    prefs = data.get("preferences", {"theme": "light", "notifications": True, "dataSharing": False})

    st.subheader("Profil")
    col1, col2 = st.columns(2)
    with col1:
        first_name = st.text_input("Ad", value=profile.get("firstName", ""))
        last_name = st.text_input("Soyad", value=profile.get("lastName", ""))
        age = st.number_input("Yaş", min_value=0, max_value=120, value=int(profile.get("age", 25)))
        gender = st.selectbox("Cinsiyet", ["Erkek", "Kadın", "Diğer"], index=["Erkek","Kadın","Diğer"].index(profile.get("gender", "Diğer")))
        education = st.selectbox(
            "Eğitim Durumu",
            ["İlkokul", "Ortaokul", "Lise", "Ön Lisans", "Lisans", "Yüksek Lisans", "Doktora", "Diğer"],
            index=max(0, ["İlkokul","Ortaokul","Lise","Ön Lisans","Lisans","Yüksek Lisans","Doktora","Diğer"].index(profile.get("educationLevel", "Diğer")))
        )
    with col2:
        med_options = [
            "Hipertansiyon", "Diyabet", "Depresyon", "Anksiyete", "Epilepsi", "Migren",
            "Uyku Bozuklukları", "Kardiyovasküler Hastalık", "Tiroid Hastalıkları", "Nörolojik Bozukluklar",
        ]
        medical_text = profile.get("medicalConditions", "")
        family_text = profile.get("familyMedicalHistory", "")
        medical_init = [m.strip() for m in medical_text.split(",") if m.strip() and m.strip() in med_options]
        family_init = [m.strip() for m in family_text.split(",") if m.strip() and m.strip() in med_options]
        medical_sel = st.multiselect("Kişisel Hastalıklar", med_options, default=medical_init)
        family_sel = st.multiselect("Ailede Görülen Hastalıklar", med_options, default=family_init)
        medical_other = st.text_input("Diğer (kişisel)", value="")
        family_other = st.text_input("Diğer (aile)", value="")

    st.subheader("Tercihler")
    theme = st.selectbox("Tema", ["light", "dark"], index=["light","dark"].index(prefs.get("theme", "light")))
    notifications = st.checkbox("Bildirimler", value=bool(prefs.get("notifications", True)))
    datashare = st.checkbox("Veri Paylaşımı", value=bool(prefs.get("dataSharing", False)))

    if st.button("Kaydet", type="primary"):
        db = get_firestore_client()
        medical_combined = ", ".join(medical_sel + ([medical_other] if medical_other else []))
        family_combined = ", ".join(family_sel + ([family_other] if family_other else []))
        db.collection("users").document(uid).set({
            "profile": {
                "firstName": first_name,
                "lastName": last_name,
                "email": st.session_state.user.get("email"),
                "age": int(age),
                "gender": gender,
                "educationLevel": education,
                "medicalConditions": medical_combined,
                "familyMedicalHistory": family_combined,
            },
            "preferences": {
                "theme": theme,
                "notifications": bool(notifications),
                "dataSharing": bool(datashare),
            },
        }, merge=True)
        st.session_state.user["profile"] = {
            "firstName": first_name,
            "lastName": last_name,
            "age": int(age),
            "gender": gender,
            "educationLevel": education,
            "medicalConditions": medical_combined,
            "familyMedicalHistory": family_combined,
        }
        st.success("Kaydedildi")