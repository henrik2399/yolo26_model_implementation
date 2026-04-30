"""
app.py — 📦 Fundkiste Schule
Kein DB-Backend — Daten leben im Session State.
Design: Material + Pixel-Grid, Space Mono + DM Sans
"""
import io
import uuid
from datetime import datetime

import streamlit as st
from PIL import Image
import pandas as pd
import plotly.graph_objects as go

# Versuch, die detector-Logik zu laden
try:
    from detector import (
        detect, load_model,
        CATEGORIES, CATEGORY_ICONS, CATEGORY_COLORS,
    )
except ImportError:
    st.error("detector.py fehlt im Verzeichnis!")
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
# WICHTIG: Zugriff über ["items"], um Konflikt mit dict.items() zu vermeiden
if "items" not in st.session_state:
    st.session_state["items"] = []


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
    data = st.session_state["items"]
    total   = len(data)
    claimed = sum(1 for i in data if i["is_claimed"])
    return {"total": total, "claimed": claimed, "missing": total - claimed}


# ══════════════════════════════════════════════════════════════
#  CSS — Dein Original-Design (Fix für Kontrast & Grid)
# ══════════════════════════════════════════════════════════════
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:opsz,wght@9..40,300;9..40,400;9..40,500;9..40,600&display=swap');

/* Hintergrund & Basis-Setup */
.stApp {
    background-color: #F2EFE9 !important;
    background-image:
        linear-gradient(rgba(0,0,0,0.045) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,0,0,0.045) 1px, transparent 1px) !important;
    background-size: 28px 28px !important;
}

/* Header / Hero */
.hero {
    background: #1C1C1C !important;
    color: #F2EFE9 !important;
    padding: 2.2rem 2.8rem;
    margin: -4rem -5rem 2.5rem -5rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    border-bottom: 3px solid #E8724A;
}
.hero-title { font-family: 'Space Mono', monospace; font-size: 2rem; font-weight: 700; }
.hero-pill { background: #E8724A; color: white; padding: 0.35rem 0.85rem; font-family: 'Space Mono', monospace; font-size: 0.72rem; }

/* Stat Cards */
.stat-card {
    background: #1C1C1C !important;
    color: #F2EFE9 !important;
    border-radius: 3px;
    padding: 1.4rem 1.2rem;
    text-align: center;
    margin-bottom: 1rem;
}
.stat-num { font-family: 'Space Mono', monospace; font-size: 2.6rem; font-weight: 700; }
.stat-lbl { font-size: 0.72rem; opacity: 0.45; text-transform: uppercase; letter-spacing: 1.5px; }

/* Item Cards */
.item-card {
    background: #ffffff !important;
    border: 1px solid #E0DDD7;
    border-radius: 3px;
    margin-bottom: 1rem;
    color: #1C1C1C;
}
.item-body { padding: 1rem; }
.item-label { font-family: 'Space Mono', monospace; font-weight: 700; font-size: 1rem; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { background: transparent; border-bottom: 2px solid #1C1C1C; }
.stTabs [data-baseweb="tab"] { font-family: 'Space Mono', monospace !important; }

/* Buttons Custom */
.stButton > button {
    background: #1C1C1C !important;
    color: #F2EFE9 !important;
    font-family: 'Space Mono', monospace !important;
    border-radius: 2px !important;
}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  HERO & STATS
# ══════════════════════════════════════════════════════════════
counts = get_counts()
rate = f"{int(counts['claimed']/counts['total']*100)}%" if counts['total'] else "–"

st.markdown(f"""
<div class="hero">
  <div>
    <div class="hero-title">📦 Fundkiste</div>
    <div style="opacity:0.6; font-size:0.9rem;">Schulisches Fundbüro · KI-gestützte Objekterkennung</div>
  </div>
  <div style="text-align:right">
    <div class="hero-pill">{counts['missing']} OFFEN</div>
    <div style="font-family:'Space Mono'; font-size:0.7rem; margin-top:0.5rem; opacity:0.5;">
        {counts['total']} GESAMT · {rate} QUOTE
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
with c1: st.markdown(f'<div class="stat-card"><div class="stat-num">{counts["missing"]}</div><div class="stat-lbl">Offen</div></div>', unsafe_allow_html=True)
with c2: st.markdown(f'<div class="stat-card"><div class="stat-num">{counts["claimed"]}</div><div class="stat-lbl">Abgeholt</div></div>', unsafe_allow_html=True)
with c3: st.markdown(f'<div class="stat-card"><div class="stat-num">{counts["total"]}</div><div class="stat-lbl">Gesamt</div></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
#  HAUPT-TABS
# ══════════════════════════════════════════════════════════════
tab_search, tab_add, tab_stats = st.tabs(["🔍 Suchen", "📷 Melden", "📊 Statistik"])

with tab_search:
    # Filter-Sektion
    col_s, col_c = st.columns([3, 2])
    with col_s: q = st.text_input("Suche", placeholder="Was suchst du?", label_visibility="collapsed")
    with col_c: cat_f = st.selectbox("Filter", ["Alle"] + CATEGORIES, label_visibility="collapsed")
    
    show_all = st.checkbox("Abgeholte zeigen")

    # Filter-Logik
    items = st.session_state["items"]
    if not show_all: items = [i for i in items if not i["is_claimed"]]
    if cat_f != "Alle": items = [i for i in items if i["category"] == cat_f]
    if q: items = [i for i in items if q.lower() in i["label"].lower()]
    
    items = list(reversed(items))

    # Grid-Anzeige
    if not items:
        st.info("Keine Einträge gefunden.")
    else:
        cols = st.columns(3)
        for idx, item in enumerate(items):
            with cols[idx % 3]:
                if item["image_bytes"]:
                    st.image(Image.open(io.BytesIO(item["image_bytes"])), use_container_width=True)
                
                st.markdown(f"""
                <div class="item-card">
                  <div class="item-body">
                    <div class="item-label">{item['label']}</div>
                    <div style="color:{CATEGORY_COLORS.get(item['category'], '#888')}; font-size:0.8rem; font-weight:bold;">
                        {CATEGORY_ICONS.get(item['category'], '📦')} {item['category']}
                    </div>
                    <div style="font-size:0.75rem; color:#666; margin-top:5px;">📍 {item['location']}</div>
                    <div style="font-size:0.65rem; color:#aaa; margin-top:10px;">{item['created_at']}</div>
                  </div>
                </div>""", unsafe_allow_html=True)
                
                if not item["is_claimed"]:
                    if st.button("Abgeholt", key=f"btn_{item['id']}"):
                        claim_item(item["id"])
                        st.rerun()

with tab_add:
    # Hier kommt die Kamera-Logik hin
    l, r = st.columns(2)
    with l:
        img_file = st.camera_input("Foto machen")
        ai_res = None
        if img_file:
            img = Image.open(img_file)
            ai_res = detect(img)
            if ai_res["success"]:
                st.success(f"KI: {ai_res['label']} ({int(ai_res['confidence']*100)}%)")
    
    with r:
        label = st.text_input("Name", value=ai_res["label"] if ai_res and ai_res["success"] else "")
        cat = st.selectbox("Kategorie", CATEGORIES, index=CATEGORIES.index(ai_res["category"]) if ai_res and ai_res["success"] else 0)
        loc = st.text_input("Ort")
        desc = st.text_area("Details")
        
        if st.button("Speichern"):
            if label:
                add_item(label, cat, loc, desc, img_file.getvalue() if img_file else None, ai_res["confidence"] if ai_res else 0)
                st.success("Gespeichert!")
                st.rerun()

with tab_stats:
    all_data = st.session_state["items"]
    if not all_data:
        st.write("Noch keine Daten.")
    else:
        df = pd.DataFrame(all_data)
        # Hier kannst du die Chart-Logik aus deinem 700-Zeilen File wieder einfügen
        st.subheader("Verteilung nach Kategorien")
        st.bar_chart(df["category"].value_counts())