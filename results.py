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


def render_results_page() -> None:
    st.title("📊 Sonuçlar")
    uid = st.session_state.user.get("uid") if st.session_state.user else None
    if not uid:
        st.warning("Giriş gerekli")
        return

    data = _fetch_user_results(uid)
    if not data:
        st.info("Henüz sonuç yok.")
        return

    df = pd.DataFrame([
        {
            "Date": (_normalize_date(r.get("metadata", {}).get("_completedAtStr") or r.get("metadata", {}).get("completedAt"))),
            "Score": r.get("score", 0),
            "Test": r.get("testType", ""),
            "Accuracy": r.get("accuracy", 0.0),
            "AvgRT": r.get("averageResponseTime", 0.0),
        }
        for r in data
    ])

    # Filters
    types = sorted(df["Test"].unique().tolist())
    selected = st.multiselect("Test Türleri", options=types, default=types)
    date_min, date_max = df["Date"].min(), df["Date"].max()
    d1, d2 = st.date_input("Tarih Aralığı", value=(date_min.date(), date_max.date()))

    fdf = df[(df["Test"].isin(selected)) & (df["Date"].dt.date >= d1) & (df["Date"].dt.date <= d2)] if not df.empty else df

    st.subheader("Zaman Bazlı Performans")
    chart = alt.Chart(fdf).mark_line(point=True).encode(
        x=alt.X("Date:T", title="Tarih"),
        y=alt.Y("Score:Q", title="Skor"),
        color=alt.Color("Test:N", title="Test Türü"),
        tooltip=["Date:T", "Test:N", "Score:Q"],
    ).properties(height=320)
    st.altair_chart(chart, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Doğruluk vs Tepki Süresi")
        scat = alt.Chart(fdf).mark_circle(size=80).encode(
            x=alt.X("AvgRT:Q", title="Ortalama RT (s)"),
            y=alt.Y("Accuracy:Q", title="Doğruluk (%)"),
            color=alt.Color("Test:N", title="Test Türü"),
            tooltip=["Date:T", "Test:N", "Accuracy:Q", "AvgRT:Q"],
        ).interactive()
        st.altair_chart(scat, use_container_width=True)
    with col2:
        st.subheader("Özet Tablosu")
        show = fdf.sort_values("Date", ascending=False).copy()
        show["Date"] = show["Date"].dt.strftime("%Y-%m-%d %H:%M")
        st.dataframe(show, use_container_width=True, hide_index=True)

    # Aggregates by test type (bar)
    st.subheader("Test Türüne Göre Ortalama Skor")
    agg = fdf.groupby("Test", as_index=False)["Score"].mean()
    bar = alt.Chart(agg).mark_bar().encode(
        x=alt.X("Test:N", title="Test Türü"),
        y=alt.Y("Score:Q", title="Ortalama Skor"),
        tooltip=["Test:N", "Score:Q"],
    )
    st.altair_chart(bar, use_container_width=True)

    # Insights placeholder (simple heuristic)
    st.subheader("Performans İçgörüleri")
    if not fdf.empty:
        best = agg.sort_values("Score", ascending=False).head(1)["Test"].values[0]
        worst = agg.sort_values("Score").head(1)["Test"].values[0]
        st.write(f"En güçlü alan: {best}. Gelişim alanı: {worst}.")
    else:
        st.write("Yeterli veri yok.")