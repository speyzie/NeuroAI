import json
import streamlit as st
from typing import Any, Dict, List
from services.firebase import get_firestore_client
from ai import ReportGenerator
from google.cloud import firestore as gfs
from datetime import datetime


def _collect_user_data(uid: str, start: datetime = None, end: datetime = None, types: List[str] = None) -> Dict[str, Any]:
    db = get_firestore_client()
    user_doc = db.collection("users").document(uid).get()
    profile = user_doc.to_dict() if user_doc.exists else {}
    results = [d.to_dict() | {"id": d.id} for d in db.collection("testResults").where("userId", "==", uid).stream()]
    # simple client-side filter
    def norm_date(r: Dict[str, Any]) -> datetime:
        v = r.get("metadata", {}).get("_completedAtStr") or r.get("metadata", {}).get("completedAt")
        try:
            return datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        except Exception:
            return datetime.utcnow()
    if start and end:
        results = [r for r in results if start <= norm_date(r) <= end]
    if types:
        results = [r for r in results if r.get("testType") in types]
    return {"profile": profile, "results": results}


def render_reports_page() -> None:
    st.title("📋 Raporlar")
    uid = st.session_state.user.get("uid") if st.session_state.user else None
    if not uid:
        st.warning("Giriş gerekli")
        return

    report_type = st.selectbox("Rapor Türü", ["general", "performance", "trend"], index=0)

    # Filters
    db = get_firestore_client()
    raw = [d.to_dict() for d in db.collection("testResults").where("userId", "==", uid).stream()]
    # dates
    def norm_date(r: Dict[str, Any]) -> datetime:
        v = r.get("metadata", {}).get("_completedAtStr") or r.get("metadata", {}).get("completedAt")
        try:
            return datetime.fromisoformat(str(v).replace("Z", "+00:00"))
        except Exception:
            return datetime.utcnow()
    dates = [norm_date(r) for r in raw] if raw else []
    if dates:
        dmin, dmax = min(dates), max(dates)
        d1, d2 = st.date_input("Tarih Aralığı", value=(dmin.date(), dmax.date()))
    else:
        d1 = d2 = None

    types = sorted(list({r.get("testType", "") for r in raw}))
    selected_types = st.multiselect("Test Türleri", options=types, default=types)

    if st.button("Rapor Oluştur", type="primary"):
        with st.spinner("Rapor oluşturuluyor..."):
            start_dt = datetime.combine(d1, datetime.min.time()) if d1 else None
            end_dt = datetime.combine(d2, datetime.max.time()) if d2 else None
            data = _collect_user_data(uid, start_dt, end_dt, selected_types)
            gen = ReportGenerator()
            text = gen.generate_report_text(data, report_type)
            pdf_path = gen.generate_pdf(text)

        st.subheader("Önizleme")
        st.text_area("İçerik", text, height=320)
        with open(pdf_path, "rb") as f:
            st.download_button("PDF İndir", f, file_name=f"neuroai_{report_type}.pdf", mime="application/pdf")

        # Log to Firestore
        get_firestore_client().collection("reports").add({
            "userId": uid,
            "reportType": report_type,
            "generatedAt": gfs.SERVER_TIMESTAMP,
            "content": text[:10000],
            "pdfUrl": "",
            "parameters": {"dateRange": {"start": str(start_dt), "end": str(end_dt)}, "testTypes": selected_types, "insights": []},
        })
        st.success("Rapor kaydedildi.")