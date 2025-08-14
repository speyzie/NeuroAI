from typing import Any, Dict

import streamlit as st
import google.generativeai as genai
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import tempfile
import datetime as dt


class ReportGenerator:
    def __init__(self) -> None:
        api_key = st.secrets.get("gemini", {}).get("api_key")
        if not api_key:
            raise RuntimeError("Gemini API anahtarı bulunamadı. secrets.toml dosyasını doldurun.")
        genai.configure(api_key=api_key)
        self.gemini_model = genai.GenerativeModel("gemini-2.5-flash")

    def _create_prompt(self, user_data: Dict[str, Any], report_type: str) -> str:
        return (
            "You are an expert neurocognitive analyst. Create a concise, structured "
            f"{report_type} report using the provided JSON data. "
            "Use headings, bullet points, and short paragraphs."
            "\n\nUSER_DATA:\n" + str(user_data)
        )

    def generate_report_text(self, user_data: Dict[str, Any], report_type: str) -> str:
        prompt = self._create_prompt(user_data, report_type)
        resp = self.gemini_model.generate_content(prompt)
        return resp.text or "Report generation failed."

    def generate_pdf(self, report_text: str) -> str:
        fd, path = tempfile.mkstemp(prefix="neuroai_report_", suffix=".pdf")
        c = canvas.Canvas(path, pagesize=A4)
        width, height = A4
        text_obj = c.beginText(40, height - 60)
        text_obj.setFont("Helvetica", 11)
        for line in report_text.splitlines() or [""]:
            for chunk in [line[i:i+100] for i in range(0, len(line), 100)]:
                text_obj.textLine(chunk)
        text_obj.textLine("")
        text_obj.textLine(f"Generated at: {dt.datetime.utcnow().isoformat()}Z")
        c.drawText(text_obj)
        c.showPage()
        c.save()
        return path