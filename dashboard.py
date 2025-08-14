import streamlit as st
import pandas as pd
import altair as alt
from services.firebase import get_firestore_client
from typing import List, Dict, Any
from datetime import datetime


def _fetch_user_results(uid: str) -> List[Dict[str, Any]]:
    db = get_firestore_client()
    docs = db.collection("testResults").where("userId", "==", uid).stream()
    results = []
    for d in docs:
        item = d.to_dict()
        item["id"] = d.id
        results.append(item)
    return results


def _normalize_date(v: Any) -> datetime:
    try:
        return datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except Exception:
        return datetime.utcnow()


def render_dashboard_page() -> None:
    # Header with close button
    col1, col2, col3 = st.columns([1, 3, 1])
    with col1:
        st.markdown("### ❌")
    with col2:
        st.markdown("""
        <h1 style='text-align: center; color: #1f77b4; font-size: 36px; margin: 20px 0;'>
            🧠 NeuroAI Dashboard
        </h1>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown("### ⋮ Deploy")
    
    st.divider()
    
    # Welcome Section
    st.markdown("""
    <div style='margin: 30px 0;'>
        <h2 style='color: white; font-size: 28px; margin: 20px 0;'>👋 Hoş Geldiniz!</h2>
        <p style='color: #cccccc; font-size: 16px; line-height: 1.6; margin: 15px 0;'>
            Bilişsel sağlığınızı takip etmeye devam edin. NeuroAI, bilişsel değerlendirme ve erken uyarı sistemi ile size yardımcı olur. Düzenli testler yaparak bilişsel performansınızı izleyebilir ve geliştirebilirsiniz.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick Statistics
    st.markdown("""
    <div style='margin: 30px 0;'>
        <h3 style='color: white; font-size: 22px; margin: 20px 0;'>📊 Hızlı İstatistikler</h3>
    </div>
    """, unsafe_allow_html=True)
    
    uid = st.session_state.user.get("uid") if st.session_state.user else None
    results = _fetch_user_results(uid) if uid else []
    
    # Demo data if no real results
    if not results:
        demo_stats = [
            ("Test Türü", "4", "📋"),
            ("Ortalama Performans", "0", "📊")
        ]
    else:
        total_tests = len(results)
        test_types = len(set(r.get("testType", "") for r in results))
        avg_performance = sum(r.get("score", 0) for r in results) / len(results) if results else 0
        demo_stats = [
            ("Test Türü", str(test_types), "📋"),
            ("Ortalama Performans", str(int(avg_performance)), "📊")
        ]
    
    # Statistics in 2 columns with better styling
    col1, col2 = st.columns(2)
    for i, (label, value, icon) in enumerate(demo_stats):
        with (col1 if i == 0 else col2):
            st.markdown(f"""
            <div style='text-align: center; padding: 30px 20px; background: linear-gradient(135deg, #1e1e1e 0%, #2a2a2a 100%); border-radius: 15px; border: 2px solid #333; margin: 10px 0; box-shadow: 0 4px 15px rgba(0,0,0,0.3);'>
                <div style='font-size: 48px; margin: 0 0 15px 0;'>{icon}</div>
                <h4 style='color: #cccccc; font-size: 16px; margin: 0 0 15px 0; font-weight: 300;'>{label}</h4>
                <h2 style='color: #ff69b4; font-size: 42px; margin: 0; font-weight: bold;'>{value}</h2>
            </div>
            """, unsafe_allow_html=True)
    
    st.divider()
    
    # Recent Activities
    st.markdown("""
    <div style='margin: 30px 0;'>
        <h3 style='color: white; font-size: 22px; margin: 20px 0;'>📈 Son Aktiviteler</h3>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <div style='background: linear-gradient(135deg, #1e1e1e 0%, #2a2a2a 100%); padding: 25px; border-radius: 15px; border: 2px solid #333; margin: 20px 0; box-shadow: 0 4px 15px rgba(0,0,0,0.3);'>
        <h4 style='color: #ff69b4; font-size: 20px; margin: 0 0 20px 0; text-align: center;'>📊 Son Test Performansı</h4>
    """, unsafe_allow_html=True)
    
    if results:
        # Real data processing
        df = pd.DataFrame([
            {
                "Date": (_normalize_date(r.get("metadata", {}).get("_completedAtStr") or r.get("metadata", {}).get("completedAt"))),
                "Score": r.get("score", 0),
                "Test": r.get("testType", "")
            }
            for r in results
        ])
        
        # Create demo-like data for better visualization
        if len(df) < 4:
            demo_dates = pd.date_range(start='2025-07-20', periods=4, freq='7D')
            demo_scores = [62, 100, 78, 88]
            df = pd.DataFrame({
                "Date": demo_dates,
                "Score": demo_scores,
                "Test": "Demo"
            })
        
        chart = alt.Chart(df).mark_line(point=True, strokeWidth=3).encode(
            x=alt.X("Date:T", title="Tarih", axis=alt.Axis(titleColor="white", labelColor="white")),
            y=alt.Y("Score:Q", title="Skor", scale=alt.Scale(domain=[50, 100]), axis=alt.Axis(titleColor="white", labelColor="white")),
            color=alt.Color("Test:N", title="Test Türü", legend=alt.Legend(titleColor="white", labelColor="white")),
            tooltip=["Date:T", "Test:N", "Score:Q"],
        ).properties(
            height=400,
            title=alt.TitleParams("Test Performansı Zaman Serisi", color="white")
        ).configure_axis(
            gridColor="#333",
            domainColor="#333"
        )
        
        st.altair_chart(chart, use_container_width=True)
        
    else:
        # Demo chart
        demo_data = pd.DataFrame({
            "Date": pd.date_range(start='2025-07-20', periods=4, freq='7D'),
            "Score": [62, 100, 78, 88],
            "Test": "Demo"
        })
        
        chart = alt.Chart(demo_data).mark_line(point=True, strokeWidth=3, color="#ff69b4").encode(
            x=alt.X("Date:T", title="Tarih", axis=alt.Axis(titleColor="white", labelColor="white")),
            y=alt.Y("Score:Q", title="Skor", scale=alt.Scale(domain=[50, 100]), axis=alt.Axis(titleColor="white", labelColor="white")),
            tooltip=["Date:T", "Score:Q"],
        ).properties(
            height=400,
            title=alt.TitleParams("Test Performansı Zaman Serisi", color="white")
        ).configure_axis(
            gridColor="#333",
            domainColor="#333"
        )
        
        st.altair_chart(chart, use_container_width=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.divider()
    
    # Action buttons
    colA, colB, colC = st.columns([1, 1, 1])
    with colA:
        if st.button("🧠 Yeni Test Başlat", type="primary", use_container_width=True):
            st.session_state.active_page = "Bilişsel Testler"
            st.rerun()
    with colB:
        if st.button("📊 Sonuçları Görüntüle", type="primary", use_container_width=True):
            st.session_state.active_page = "Sonuçlar"
            st.rerun()
    with colC:
        if st.button("📋 Rapor Oluştur", type="primary", use_container_width=True):
            st.session_state.active_page = "Raporlar"
            st.rerun()