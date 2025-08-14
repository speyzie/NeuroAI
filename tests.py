import time
import random
import datetime as dt
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import streamlit as st
from services.firebase import get_firestore_client
from google.cloud import firestore as gfs


@dataclass
class ResponseItem:
    questionId: str
    response: Any
    correct: bool
    responseTime: float
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CognitiveTest:
    test_type: str
    phase: str = "instructions"  # instructions | practice | main | finished
    questions: List[Dict[str, Any]] = field(default_factory=list)
    practice_questions: List[Dict[str, Any]] = field(default_factory=list)
    responses: List[ResponseItem] = field(default_factory=list)
    practice_responses: List[ResponseItem] = field(default_factory=list)
    current_index: int = 0
    started_at: float = 0.0
    question_started_at: float = 0.0
    question_runtime_meta: Dict[str, Any] = field(default_factory=dict)

    def start(self) -> None:
        self.started_at = time.time()
        self.current_index = 0
        self.question_started_at = time.time()

    def load_questions(self) -> None:
        if self.test_type == "memory":
            self.practice_questions = generate_memory_questions(3)
            self.questions = generate_memory_questions(20)
        elif self.test_type == "attention":
            self.practice_questions = generate_attention_questions(3)
            self.questions = generate_attention_questions(20)
        elif self.test_type == "stroop":
            self.practice_questions = generate_stroop_trials(5)
            self.questions = generate_stroop_trials(20)
        else:
            self.practice_questions = []
            self.questions = []

    def _active_question_list(self) -> List[Dict[str, Any]]:
        return self.practice_questions if self.phase == "practice" else self.questions

    def current_question(self) -> Dict[str, Any]:
        return self._active_question_list()[self.current_index]

    def record_response(self, user_input: Any) -> None:
        q = self.current_question()
        rt = max(0.0, time.time() - self.question_started_at)
        is_correct, meta = evaluate_answer(self.test_type, q, user_input, self.question_runtime_meta)
        item = ResponseItem(q.get("id"), user_input, is_correct, rt, meta)
        if self.phase == "practice":
            self.practice_responses.append(item)
        else:
            self.responses.append(item)
        self.current_index += 1
        if self.current_index < len(self._active_question_list()):
            self.question_started_at = time.time()
            self.question_runtime_meta = {}

    def is_finished_phase(self) -> bool:
        return self.current_index >= len(self._active_question_list())

    def advance_phase(self) -> None:
        if self.phase == "instructions":
            self.phase = "practice"
        elif self.phase == "practice":
            self.phase = "main"
        elif self.phase == "main":
            self.phase = "finished"
        self.current_index = 0
        self.question_started_at = time.time()
        self.question_runtime_meta = {}

    def calculate_metrics(self) -> Dict[str, Any]:
        data = self.responses
        if not data:
            return {"score": 0, "accuracy": 0.0, "avg_rt": 0.0}
        correct_count = sum(1 for r in data if r.correct)
        accuracy = correct_count / len(data) * 100.0
        avg_rt = sum(r.responseTime for r in data) / len(data)
        metrics: Dict[str, Any] = {
            "score": correct_count,
            "accuracy": round(accuracy, 2),
            "avg_rt": round(avg_rt, 3),
        }
        # Stroop extras
        if self.test_type == "stroop":
            congruent_rts = [r.responseTime for r in data if r.meta.get("condition") == "congruent"]
            incongruent_rts = [r.responseTime for r in data if r.meta.get("condition") == "incongruent"]
            stroop_effect = (sum(incongruent_rts)/len(incongruent_rts) - sum(congruent_rts)/len(congruent_rts)) if (congruent_rts and incongruent_rts) else 0.0
            metrics.update({
                "stroop_effect": round(stroop_effect, 3),
                "error_rate": round(100 - accuracy, 2),
            })
        return metrics

    def save_results(self, uid: str) -> None:
        db = get_firestore_client()
        metrics = self.calculate_metrics()
        payload = {
            "userId": uid,
            "testType": self.test_type,
            "score": metrics.get("score", 0),
            "accuracy": metrics.get("accuracy", 0.0),
            "averageResponseTime": metrics.get("avg_rt", 0.0),
            "responses": [r.__dict__ for r in self.responses],
            "metadata": {
                "duration": max(0.0, time.time() - self.started_at),
                "completedAt": gfs.SERVER_TIMESTAMP,
                "_completedAtStr": dt.datetime.utcnow().isoformat() + "Z",
            },
            "analysis": {
                "strengths": [],
                "weaknesses": [],
                "percentileRank": 0,
            },
        }
        if self.test_type == "stroop":
            payload["analysis"].update({
                "stroopEffect": self.calculate_metrics().get("stroop_effect", 0.0),
                "errorRate": 100 - self.calculate_metrics().get("accuracy", 0.0),
            })
        db.collection("testResults").add(payload)


# ---------- Question Generators and Evaluators ----------

COMMON_WORDS = [
    "elma", "nehir", "masa", "yeşil", "müzik", "ev", "dağ", "okyanus", "pencere", "gölge",
    "hafıza", "kalem", "bahçe", "portakal", "gezegen", "gümüş", "mum", "orman", "köprü", "bulut",
]

COLORS = [
    ("KIRMIZI", "red"), ("MAVI", "blue"), ("YESIL", "green"), ("SARI", "yellow"), ("MOR", "purple"), ("SIYAH", "black")
]


def generate_memory_questions(n: int) -> List[Dict[str, Any]]:
    qs: List[Dict[str, Any]] = []
    for i in range(n):
        t = i % 4
        if t == 0:
            # Word list recall (encoding then recall)
            words = random.sample(COMMON_WORDS, k=8)
            qs.append({
                "id": f"mem_words_{i+1}",
                "type": "word_list_recall",
                "words": words,
                "encode_seconds": 8,
                "input": "text",
            })
        elif t == 1:
            # Number sequence
            length = random.randint(5, 8)
            digits = "".join(str(random.randint(0, 9)) for _ in range(length))
            qs.append({
                "id": f"mem_num_{i+1}",
                "type": "number_sequence",
                "digits": digits,
                "encode_seconds": 3,
                "input": "text",
            })
        elif t == 2:
            # Visual 3x3 pattern (positions 1-9)
            positions = sorted(random.sample(list(range(1, 10)), k=random.randint(3, 5)))
            qs.append({
                "id": f"mem_pattern_{i+1}",
                "type": "pattern_3x3",
                "positions": positions,
                "encode_seconds": 4,
                "input": "multiselect",
                "options": list(range(1, 10)),
            })
        else:
            # Paired associates (word-number), ask number for cue
            pairs = [(random.choice(COMMON_WORDS), random.randint(10, 99)) for _ in range(5)]
            cue, ans = random.choice(pairs)
            qs.append({
                "id": f"mem_pairs_{i+1}",
                "type": "paired_associate",
                "pairs": pairs,
                "cue": cue,
                "answer": ans,
                "encode_seconds": 7,
                "input": "text",
            })
    return qs


def generate_attention_questions(n: int) -> List[Dict[str, Any]]:
    questions: List[Dict[str, Any]] = []
    for i in range(n):
        if i % 2 == 0:
            letters = [random.choice(list("ABCDEFGHJKLMNPRSTUVWXYZ")) for _ in range(24)]
            target = random.choice(["X", "Z"])  # sometimes absent
            present = random.choice([True, False])
            if present:
                letters[random.randrange(len(letters))] = target
            seq = " ".join(letters)
            questions.append({
                "id": f"att_present_{i+1}",
                "type": "target_present",
                "sequence": seq,
                "target": target,
                "answer": present,
                "input": "buttons",
                "options": ["Var", "Yok"],
            })
        else:
            letters = [random.choice(list("ABCDEFXGHIJKLMNOPQRSTUXVWXYZ")) for _ in range(36)]
            target = random.choice(["A", "E", "X"])
            count = sum(1 for ch in letters if ch == target)
            seq = " ".join(letters)
            questions.append({
                "id": f"att_count_{i+1}",
                "type": "target_count",
                "sequence": seq,
                "target": target,
                "answer": count,
                "input": "text",
            })
    return questions


def generate_stroop_trials(n: int) -> List[Dict[str, Any]]:
    """Generate Stroop test questions with proper congruent/incongruent trials"""
    questions: List[Dict[str, Any]] = []
    
    # Color definitions with hex codes
    colors = [
        ("KIRMIZI", "red", "#FF0000"),
        ("MAVI", "blue", "#0000FF"), 
        ("YESIL", "green", "#00FF00"),
        ("SARI", "yellow", "#FFFF00"),
        ("MOR", "purple", "#800080"),
        ("SIYAH", "black", "#000000")
    ]
    
    for i in range(n):
        # Randomly select a word and its meaning
        word_tr, word_en, word_hex = random.choice(colors)
        
        # 50% chance for congruent vs incongruent
        if random.random() < 0.5:
            # Congruent: word meaning matches ink color
            condition = "congruent"
            ink_color = word_en
            ink_hex = word_hex
        else:
            # Incongruent: word meaning differs from ink color
            condition = "incongruent"
            # Choose a different color for ink
            other_colors = [(w, c, h) for w, c, h in colors if c != word_en]
            _, ink_color, ink_hex = random.choice(other_colors)
        
        questions.append({
            "id": f"stroop_{i+1}",
            "type": "stroop",
            "word": word_tr,  # The word to display
            "ink_color": ink_color,  # English color name for logic
            "ink_hex": ink_hex,  # Hex code for display
            "condition": condition,
            "answer": ink_color,  # User should select the ink color
            "input": "buttons",
        })
    return questions


def evaluate_answer(test_type: str, q: Dict[str, Any], user_input: Any, runtime_meta: Dict[str, Any]) -> (bool, Dict[str, Any]):
    meta: Dict[str, Any] = {}
    if test_type == "memory":
        if q["type"] == "word_list_recall":
            presented = {w.strip().lower() for w in q.get("words", [])}
            typed = {w.strip().lower() for w in str(user_input).replace("\n", " ").split(" ") if w.strip()}
            recalled = len(presented.intersection(typed))
            meta.update({"recalled": recalled, "total": len(presented)})
            return recalled >= max(1, len(presented)//3), meta
        if q["type"] == "number_sequence":
            return str(user_input).strip() == str(q.get("digits", "")).strip(), meta
        if q["type"] == "pattern_3x3":
            try:
                sel = sorted([int(x) for x in (user_input or [])])
            except Exception:
                sel = []
            correct = sel == sorted(q.get("positions", []))
            meta.update({"selected": sel, "expected": q.get("positions", [])})
            return correct, meta
        if q["type"] == "paired_associate":
            try:
                return int(str(user_input).strip()) == int(q.get("answer")), meta
            except Exception:
                return False, meta
        return False, meta
    if test_type == "attention":
        if q["type"] == "target_present":
            expected = "Var" if q.get("answer") else "Yok"
            return user_input == expected, meta
        if q["type"] == "target_count":
            try:
                return int(user_input) == int(q.get("answer", 0)), meta
            except Exception:
                return False, meta
    if test_type == "stroop":
        meta["condition"] = q.get("condition")
        # Compare user's selection with the ink color (not the word meaning)
        return user_input == q.get("answer"), meta
    return False, meta


# ---------- UI Rendering ----------

def _ensure_test_state() -> None:
    if "test_state" not in st.session_state:
        st.session_state.test_state = {
            "active": False,
            "type": "memory",
            "engine": None,
        }


def _start_test(selected: str) -> None:
    engine = CognitiveTest(selected)
    engine.load_questions()
    engine.start()
    engine.phase = "instructions"
    st.session_state.test_state.update({
        "active": True,
        "type": selected,
        "engine": engine,
    })


def _render_instructions(engine: CognitiveTest) -> None:
    names = {
        "memory": "Hafıza Testi",
        "attention": "Dikkat Testi",
        "reaction": "Reaksiyon Süresi Testi",
        "stroop": "Stroop Testi",
    }
    st.subheader(f"{names.get(engine.test_type, engine.test_type)} | Talimatlar")
    if engine.test_type == "memory":
        st.markdown("- Kelime listeleri, sayı dizileri, görsel desenler ve eşleştirmeler gösterilecek.\n- Önce kısa deneme, sonra 20 soruluk ana test.\n- Uyarı: Uyarı ekranından sonra uyaran kaybolur, hatırlayıp girmeniz beklenir.")
    elif engine.test_type == "attention":
        st.markdown("- Dikkat ölçümleri için hedef var/yok ve sayma görevleri.\n- Önce deneme, sonra ana test.")
    elif engine.test_type == "reaction":
        st.markdown("- Rasgele bekleme sonrası GO görünür. Hızla tıklayın.\n- Bazı denemelerde seçim yapın veya NO-GO’da tıklamayın.")
    elif engine.test_type == "stroop":
        st.markdown("- Kelimenin YAZI RENGİNİ seçin (kelimeyi değil).\n- 5 deneme, 20 soru.")
    if st.button("Denemeye Başla", type="primary"):
        engine.advance_phase()  # to practice
        st.rerun()


def _render_progress(engine: CognitiveTest) -> None:
    total = len(engine._active_question_list())
    st.progress(int((engine.current_index/total)*100) if total else 0)
    st.caption(f"Soru {engine.current_index+1}/{total} | Aşama: {engine.phase}")


def _render_memory_question(q: Dict[str, Any], engine: CognitiveTest) -> None:
    stage = engine.question_runtime_meta.get("stage", "encode")

    if stage == "encode":
        # Display stimulus
        if q["type"] == "word_list_recall":
            st.info("Kelime listesi (ezberleyin):")
            st.write(", ".join(q.get("words", [])))
        elif q["type"] == "number_sequence":
            st.info("Sayı dizisi (ezberleyin):")
            st.markdown(f"<h2 style='text-align:center'>{q.get('digits','')}</h2>", unsafe_allow_html=True)
        elif q["type"] == "pattern_3x3":
            st.info("Deseni aklınızda tutun (pozisyonlar 1-9):")
            _render_grid(q.get("positions", []))
        elif q["type"] == "paired_associate":
            st.info("Eşleştirmeleri aklınızda tutun (kelime → sayı):")
            st.write("; ".join([f"{w}→{n}" for w, n in q.get("pairs", [])]))
        
        # Manual advance button
        if st.button("Hatırlamaya Geç"):
            engine.question_runtime_meta["stage"] = "recall"
            st.rerun()
    else:
        # Recall stage (no stimulus)
        if q["type"] == "word_list_recall":
            ans = st.text_area("Hatırladıklarınızı yazın (boşlukla ayırın)", height=100)
            if st.button("Gönder"):
                engine.record_response(ans)
                st.rerun()
        elif q["type"] == "number_sequence":
            ans = st.text_input("Gördüğünüz sayı dizisini yazın")
            if st.button("Gönder"):
                engine.record_response(ans)
                st.rerun()
        elif q["type"] == "pattern_3x3":
            options = [1,2,3,4,5,6,7,8,9]
            sel = st.multiselect("Gördüğünüz pozisyonları seçin", options)
            if st.button("Gönder"):
                engine.record_response(sel)
                st.rerun()
        elif q["type"] == "paired_associate":
            st.write(f"İpucu: {q.get('cue')}")
            ans = st.text_input("Eşleşen sayıyı yazın")
            if st.button("Gönder"):
                engine.record_response(ans)
                st.rerun()


def _render_grid(positions: List[int]) -> None:
    # 3x3 grid, highlight positions
    mapping = {pos: "#4a90e2" for pos in positions}
    for row in range(3):
        cols = st.columns(3)
        for col in range(3):
            idx = row*3 + col + 1
            color = mapping.get(idx, "#ddd")
            cols[col].markdown(
                f"""
                <div style='height:60px;border:1px solid #ccc;background:{color};display:flex;align-items:center;justify-content:center;'>
                {idx}
                </div>
                """,
                unsafe_allow_html=True,
            )


def _render_question(engine: CognitiveTest) -> None:
    q = engine.current_question()
    st.container()
    st.write("")
    st.write("")
    input_type = q.get("input")

    # Memory special flow
    if engine.test_type == "memory":
        _render_memory_question(q, engine)
        return

    # Attention
    if engine.test_type == "attention":
        if q["type"] in ("target_present", "target_count"):
            st.info(f"Hedef: {q.get('target')}\n\n{q.get('sequence')}")
            if q["type"] == "target_present":
                cols = st.columns(2)
                clicked = None
                for idx, opt in enumerate(q.get("options", [])):
                    if cols[idx].button(opt):
                        clicked = opt
                if clicked is not None:
                    engine.record_response(clicked)
                    st.rerun()
            else:
                val = st.text_input("Adet")
                if st.button("Gönder"):
                    engine.record_response(val)
                    st.rerun()
        return

    # Stroop
    if engine.test_type == "stroop":
        st.info("Kelimenin RENK mürekkebini seçin (kelimeyi değil)")
        
        # Get question data
        word = q.get('word', '')
        ink_hex = q.get('ink_hex', '#FFFFFF')
        
        # Display the word in its ink color
        st.markdown(f"""
        <div style="text-align: center; margin: 40px 0;">
            <span style="color: {ink_hex}; font-size: 72px; font-weight: bold; display: block;">
                {word}
            </span>
        </div>
        """, unsafe_allow_html=True)
        
        # Turkish color options
        color_options = ["KIRMIZI", "MAVI", "YESIL", "SARI", "MOR", "SIYAH"]
        color_map = {
            "KIRMIZI": "red",
            "MAVI": "blue", 
            "YESIL": "green",
            "SARI": "yellow",
            "MOR": "purple",
            "SIYAH": "black"
        }
        
        # Show color selection buttons
        cols = st.columns(3)
        clicked = None
        for idx, opt in enumerate(color_options):
            if cols[idx % 3].button(opt, use_container_width=True):
                clicked = opt
        
        if clicked is not None:
            # Convert Turkish selection to English for answer comparison
            english_color = color_map.get(clicked, clicked)
            engine.record_response(english_color)
            st.rerun()
        return

    st.write("Bu soru tipi desteklenmiyor.")


def _render_phase(engine: CognitiveTest) -> None:
    if engine.phase == "instructions":
        _render_instructions(engine)
        return

    if engine.is_finished_phase():
        if engine.phase == "practice":
            st.success("Deneme tamamlandı. Kısa geribildirim:")
            pr = engine.practice_responses
            if pr:
                acc = round(sum(1 for r in pr if r.correct)/len(pr)*100.0, 1)
                st.metric("Deneme Doğruluk", f"{acc}%")
            if st.button("Ana Teste Başla", type="primary"):
                engine.advance_phase()  # to main
                st.rerun()
            return
        if engine.phase == "main":
            engine.advance_phase()  # finished
            st.rerun()
            return

    _render_progress(engine)
    _render_question(engine)


def render_tests_page() -> None:
    # Header
    st.markdown("""
    <h1 style='color: white; font-size: 36px; margin: 20px 0; text-align: center;'>
        🧠 Bilişsel Testler
    </h1>
    """, unsafe_allow_html=True)
    
    st.markdown("""
    <p style='color: #cccccc; font-size: 18px; text-align: center; margin: 20px 0;'>
        Bilişsel performansınızı değerlendirmek için aşağıdaki testlerden birini seçin.
    </p>
    """, unsafe_allow_html=True)
    
    _ensure_test_state()
    state = st.session_state.test_state

    test_map = {
        "Bellek Testi": "memory",
        "Dikkat Testi": "attention",
        "Stroop Testi": "stroop",
    }
    labels = list(test_map.keys())
    default_idx = labels.index("Bellek Testi") if state.get("type") == "memory" else 0
    
    # Test selection in a styled container
    st.markdown("""
    <div style='background-color: #1e1e1e; padding: 20px; border-radius: 10px; border: 1px solid #333; margin: 20px 0;'>
        <h3 style='color: white; margin: 0 0 15px 0;'>Test Türü Seçin:</h3>
    """, unsafe_allow_html=True)
    
    choice = st.selectbox("Test Türü Seçin", labels, index=default_idx, label_visibility="collapsed")
    selected_code = test_map[choice]
    
    st.markdown("</div>", unsafe_allow_html=True)

    # Test description
    test_descriptions = {
        "Bellek Testi": "Kelime çiftlerini öğrenip hatırlama yeteneğinizi test eder.",
        "Dikkat Testi": "Dikkat süresi ve odaklanma yeteneğinizi ölçer.",
        "Stroop Testi": "Bilişsel esneklik ve dikkat kontrolünüzü değerlendirir."
    }
    
    st.markdown(f"""
    <div style='background-color: #1e1e1e; padding: 20px; border-radius: 10px; border: 1px solid #333; margin: 20px 0;'>
        <h3 style='color: #ff69b4; margin: 0 0 15px 0;'>🧠 {choice}</h3>
        <p style='color: #cccccc; margin: 0;'>{test_descriptions.get(choice, '')}</p>
    </div>
    """, unsafe_allow_html=True)

    if not state["active"] or state["type"] != selected_code:
        if st.button("Testi Başlat", type="primary", use_container_width=True):
            _start_test(selected_code)
            st.rerun()
        return

    engine: CognitiveTest = state["engine"]
    if engine is None:
        st.warning("Test başlatılamadı.")
        return

    _render_phase(engine)

    if engine.phase == "finished":
        metrics = engine.calculate_metrics()
        
        # Results in styled container
        st.markdown("""
        <div style='background-color: #1e1e1e; padding: 20px; border-radius: 10px; border: 1px solid #333; margin: 20px 0;'>
            <h3 style='color: #ff69b4; margin: 0 0 20px 0; text-align: center;'>🎉 Test Tamamlandı!</h3>
        </div>
        """, unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Skor", metrics.get("score", 0))
        c2.metric("Doğruluk", f"{metrics.get('accuracy', 0.0)}%")
        c3.metric("Ortalama RT", f"{metrics.get('avg_rt', 0.0)} s")
        
        if engine.test_type == "stroop":
            st.metric("Stroop Etkisi", f"{metrics.get('stroop_effect', 0.0)} s")

        # Auto-save results to avoid loss
        uid = st.session_state.user.get("uid") if st.session_state.user else None
        if uid and not st.session_state.get("_saved_last_result"):
            engine.save_results(uid)
            st.session_state["_saved_last_result"] = True
            st.success("Sonuçlar kaydedildi.")

        if st.button("🏠 Ana Sayfaya Dön", type="primary", use_container_width=True):
            st.session_state.test_state = {"active": False, "type": selected_code, "engine": None}
            st.session_state.active_page = "Ana Sayfa"
            st.session_state["_saved_last_result"] = False
            st.rerun()