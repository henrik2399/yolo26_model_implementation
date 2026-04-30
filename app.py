import io
import uuid
from datetime import datetime

import streamlit as st
from PIL import Image
import pandas as pd
import plotly.graph_objects as go

# Falls deine detector.py noch nicht existiert, erstelle sie mit einer detect-Funktion
try:
    from detector import (
        detect, load_model,
        CATEGORIES, CATEGORY_ICONS, CATEGORY_COLORS,
    )
except ImportError:
    st.error("Datei 'detector.py' nicht gefunden! Bitte stelle sicher, dass sie im gleichen Ordner liegt.")
    st.stop()

# ══════════════════════════════════════════════════════════════
#  CONFIG
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Fundkiste",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ══════════════════════════════════════════════════════════════
#  SESSION STATE INITIALISIEREN
# ══════════════════════════════════════════════════════════════
# WICHTIG: Nutze ["items"], um Kollisionen mit der Methode .items() zu vermeiden
if "items" not in st.session_state:
    st.session_state["items"] = []         # Liste aller Fundobjekte


def add_item(label, category, location, description, image_bytes, confidence):
    st.session_state["items"].append({
        "id":          str(uuid.uuid4()),
        "label":       label,
        "category":    category,
        "location":    location,
        "description": description,
        "image_bytes": image_bytes,
        "confidence":  confidence,
        "is_claimed":  False,
        "created_at":  datetime.now().strftime("%d.%m.%Y %H:%M"),
    })


def claim_item(item_id):
    for item in st.session_state["items"]:
        if item["id"] == item_id:
            item["is_claimed"] = True
            item["claimed_at"] = datetime.now().strftime("%d.%m.%Y %H:%M")
            break


def get_counts():
    # .items ist eine Methode von Dicts, daher Zugriff über Key-String
    all_items = st.session_state["items"]
    total   = len(all_items)
    claimed = sum(1 for i in all_items if i["is_claimed"])
    return {"total": total, "claimed": claimed, "missing": total - claimed}


# ══════════════════════════════════════════════════════════════
#  CSS — Material + Pixel Grid
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
    background: #F2EFE9;
    color: #1C1C1C;
}

.stApp {
    background-color: #F2EFE9;
    background-image:
        linear-gradient(rgba(0,0,0,0.045) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,0,0,0.045) 1px, transparent 1px);
    background-size: 28px 28px;
}

#MainMenu, footer, header, .stDeployButton { display: none !important; }
.block-container { padding: 0 2rem 4rem; max-width: 1380px; }

.hero {
    background: #1C1C1C;
    color: #F2EFE9;
    padding: 2.2rem 2.8rem;
    margin: 0 -2rem 2.5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 3px solid #E8724A;
    position: relative;
    overflow: hidden;
}
.hero-title { font-family: 'Space Mono', monospace; font-size: 2rem; font-weight: 700; letter-spacing: -1px; }
.hero-sub { font-size: 0.88rem; opacity: 0.5; margin-top: 0.25rem; font-family: 'DM Sans', sans-serif; }
.hero-pill { background: #E8724A; color: #fff; font-family: 'Space Mono', monospace; font-size: 0.72rem; padding: 0.35rem 0.85rem; border-radius: 2px; }

.stat-card { background: #1C1C1C; color: #F2EFE9; border-radius: 3px; padding: 1.4rem 1.2rem; text-align: center; position: relative; }
.stat-card.s-orange::after { content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 3px; background: #E8724A; }
.stat-card.s-green::after  { content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 3px; background: #2ECC71; }
.stat-card.s-blue::after   { content: ''; position: absolute; bottom: 0; left: 0; right: 0; height: 3px; background: #4A90D9; }
.stat-num { font-family: 'Space Mono', monospace; font-size: 2.6rem; font-weight: 700; }
.stat-lbl { font-size: 0.72rem; opacity: 0.45; text-transform: uppercase; letter-spacing: 1.5px; }

.item-card { background: #fff; border: 1px solid #E0DDD7; border-radius: 3px; overflow: hidden; margin-bottom: 1rem; }
.item-body { padding: 0.9rem 1rem; }
.item-label { font-family: 'Space Mono', monospace; font-size: 0.9rem; font-weight: 700; color: #1C1C1C; }
.item-cat-badge { display: inline-block; font-size: 0.7rem; font-weight: 600; padding: 0.18rem 0.55rem; border-radius: 2px; }
.claimed-badge { background: #2ECC71; color: #fff; font-size: 0.6rem; padding: 0.18rem 0.45rem; border-radius: 2px; }

.ai-box { background: #1C1C1C; color: #F2EFE9; border-radius: 3px; padding: 1.1rem 1.3rem; margin: 0.8rem 0; border-left: 4px solid #E8724A; display: flex; align-items: flex-start; gap: 1rem; }
.conf-wrap { background: #EEE; border-radius: 2px; height: 3px; overflow: hidden; }
.conf-bar { height: 100%; background: #E8724A; }

.stButton > button { font-family: 'Space Mono', monospace !important; border-radius: 2px !important; background: #1C1C1C !important; color: #F2EFE9 !important; width: 100%; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  HERO / HEADER
# ══════════════════════════════════════════════════════════════
counts = get_counts()
rate   = f"{int(counts['claimed']/counts['total']*100)}%" if counts['total'] > 0 else "–"

st.markdown(f"""
<div class="hero">
  <div>
    <div class="hero-title">📦 Fundkiste</div>
    <div class="hero-sub">Schulisches Fundbüro · KI-gestützte Objekterkennung</div>
  </div>
  <div class="hero-right" style="text-align:right;">
    <div class="hero-pill">{counts['missing']} OFFEN</div>
    <div style="font-family:'Space Mono',monospace; font-size:0.68rem; opacity:0.4; margin-top:0.5rem;">
        {counts['total']} GESAMT &nbsp;·&nbsp; {counts['claimed']} ABGEHOLT &nbsp;·&nbsp; {rate} QUOTE
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
with c1:
    st.markdown(f'<div class="stat-card s-orange"><div class="stat-num">{counts["missing"]}</div><div class="stat-lbl">Noch offen</div></div>', unsafe_allow_html=True)
with c2:
    st.markdown(f'<div class="stat-card s-green"><div class="stat-num">{counts["claimed"]}</div><div class="stat-lbl">Abgeholt</div></div>', unsafe_allow_html=True)
with c3:
    st.markdown(f'<div class="stat-card s-blue"><div class="stat-num">{counts["total"]}</div><div class="stat-lbl">Insgesamt</div></div>', unsafe_allow_html=True)

st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  TABS
# ══════════════════════════════════════════════════════════════
tab_search, tab_add, tab_stats = st.tabs(["🔍 Objekt suchen", "📷 Objekt melden", "📊 Statistiken"])

# TAB: SUCHEN
with tab_search:
    col_s, col_c = st.columns([3, 2])
    with col_s:
        q = st.text_input("", placeholder="🔍 Trinkflasche, Rucksack...", label_visibility="collapsed")
    with col_c:
        cat_filter = st.selectbox("", ["Alle"] + CATEGORIES, label_visibility="collapsed")

    show_claimed = st.checkbox("Bereits abgeholte Objekte anzeigen", value=False)

    items = st.session_state["items"]
    if not show_claimed:
        items = [i for i in items if not i["is_claimed"]]
    if cat_filter != "Alle":
        items = [i for i in items if i["category"] == cat_filter]
    if q:
        items = [i for i in items if q.lower() in i["label"].lower() or q.lower() in i.get("description","").lower()]

    items = list(reversed(items))
    st.markdown(f'<div style="font-family:\'Space Mono\',monospace; font-size:0.72rem; color:#999; margin:1.5rem 0 0.8rem; text-transform:uppercase;">{len(items)} Objekte gefunden</div>', unsafe_allow_html=True)

    if not items:
        st.info("Keine Objekte in dieser Auswahl.")
    else:
        cols = st.columns(3)
        for idx, item in enumerate(items):
            col = cols[idx % 3]
            with col:
                cat = item["category"]
                icon = CATEGORY_ICONS.get(cat, "📦")
                color = CATEGORY_COLORS.get(cat, "#888")
                conf = int((item.get("confidence") or 0) * 100)
                
                # Card Rendering
                if item.get("image_bytes"):
                    st.image(Image.open(io.BytesIO(item["image_bytes"])), use_container_width=True)
                
                claimed_status = '<span class="claimed-badge">✓ ABGEHOLT</span>' if item["is_claimed"] else ""
                
                st.markdown(f"""
                <div class="item-card">
                  <div class="item-body">
                    <div style="display:flex; justify-content:space-between;">
                        <div class="item-label">{item['label']}</div>
                        {claimed_status}
                    </div>
                    <span class="item-cat-badge" style="background:{color}22; color:{color};">{icon} {cat}</span>
                    <div style="font-size:0.75rem; color:#888;">📍 {item.get('location','')}</div>
                    <div style="font-family:'Space Mono',monospace; font-size:0.65rem; color:#BBB; margin-top:0.5rem;">Gemeldet: {item['created_at']}</div>
                  </div>
                </div>""", unsafe_allow_html=True)
                
                if not item["is_claimed"]:
                    if st.button("Abgeholt", key=f"cl_{item['id']}"):
                        claim_item(item["id"])
                        st.rerun()

# TAB: MELDEN
with tab_add:
    left, right = st.columns(2, gap="large")
    raw = None
    with left:
        st.subheader("Foto")
        upload_tab, cam_tab = st.tabs(["📁 Datei", "📷 Kamera"])
        with upload_tab:
            raw = st.file_uploader("Bild wählen", type=["jpg","jpeg","png"], label_visibility="collapsed")
        with cam_tab:
            cam = st.camera_input("Kamera", label_visibility="collapsed")
            if cam: raw = cam

        ai_result = None
        if raw:
            pil_img = Image.open(raw)
            st.image(pil_img, use_container_width=True)
            with st.spinner("KI analysiert..."):
                ai_result = detect(pil_img)
            
            if ai_result["success"]:
                st.success(f"Erkannt: {ai_result['label']} ({int(ai_result['confidence']*100)}%)")

    with right:
        st.subheader("Objektdaten")
        d_label = ai_result["label"] if ai_result and ai_result["success"] else ""
        d_cat = ai_result["category"] if ai_result and ai_result["success"] else "Sonstiges"
        
        label = st.text_input("Bezeichnung *", value=d_label)
        category = st.selectbox("Kategorie *", CATEGORIES, index=CATEGORIES.index(d_cat) if d_cat in CATEGORIES else 0)
        location = st.text_input("Fundort")
        description = st.text_area("Beschreibung")

        if st.button("📦 In Fundkiste speichern"):
            if label:
                add_item(label, category, location, description, raw.getvalue() if raw else None, ai_result["confidence"] if ai_result else 0)
                st.success("Hinzugefügt!")
                st.balloons()
            else:
                st.error("Bitte Bezeichnung angeben.")

# TAB: STATS
with tab_stats:
    all_items = st.session_state["items"]
    if not all_items:
        st.write("Noch keine Daten vorhanden.")
    else:
        df = pd.DataFrame(all_items)
        st.bar_chart(df["category"].value_count())