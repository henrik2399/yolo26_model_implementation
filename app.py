"""
app.py — 📦 Fundkiste Schule
Kein DB-Backend — Daten leben im Session State (pro Browser-Session).
Design: Material + Pixel-Grid, Space Mono + DM Sans
"""
import io
import uuid
from datetime import datetime

import streamlit as st
from PIL import Image
import pandas as pd
import plotly.graph_objects as go

from detector import (
    detect, load_model,
    CATEGORIES, CATEGORY_ICONS, CATEGORY_COLORS,
)

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
if "items" not in st.session_state:
    st.session_state["items"] = []          # Liste aller Fundobjekte


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
    total   = len(st.session_state["items"])
    claimed = sum(1 for i in st.session_state["items"] if i["is_claimed"])
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

/* Pixel grid background */
.stApp {
    background-color: #F2EFE9;
    background-image:
        linear-gradient(rgba(0,0,0,0.045) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,0,0,0.045) 1px, transparent 1px);
    background-size: 28px 28px;
}

#MainMenu, footer, header, .stDeployButton { display: none !important; }
.block-container { padding: 0 2rem 4rem; max-width: 1380px; }

/* ── Hero ── */
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
.hero::before {
    content: '';
    position: absolute; inset: 0;
    background-image:
        linear-gradient(rgba(255,255,255,0.025) 1px, transparent 1px),
        linear-gradient(90deg, rgba(255,255,255,0.025) 1px, transparent 1px);
    background-size: 28px 28px;
    pointer-events: none;
}
.hero-title {
    font-family: 'Space Mono', monospace;
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: -1px;
    position: relative;
}
.hero-sub {
    font-size: 0.88rem;
    opacity: 0.5;
    margin-top: 0.25rem;
    position: relative;
    font-family: 'DM Sans', sans-serif;
}
.hero-right { text-align: right; position: relative; }
.hero-pill {
    background: #E8724A;
    color: #fff;
    font-family: 'Space Mono', monospace;
    font-size: 0.72rem;
    font-weight: 700;
    padding: 0.35rem 0.85rem;
    border-radius: 2px;
    letter-spacing: 0.5px;
    display: inline-block;
}
.hero-meta {
    font-family: 'Space Mono', monospace;
    font-size: 0.68rem;
    opacity: 0.4;
    margin-top: 0.5rem;
}

/* ── Stat Cards ── */
.stat-card {
    background: #1C1C1C;
    color: #F2EFE9;
    border-radius: 3px;
    padding: 1.4rem 1.2rem;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.stat-card::after {
    content: '';
    position: absolute;
    bottom: 0; left: 0; right: 0;
    height: 3px;
}
.stat-card.s-orange::after { background: #E8724A; }
.stat-card.s-green::after  { background: #2ECC71; }
.stat-card.s-blue::after   { background: #4A90D9; }
.stat-num {
    font-family: 'Space Mono', monospace;
    font-size: 2.6rem;
    font-weight: 700;
    line-height: 1;
}
.stat-lbl {
    font-size: 0.72rem;
    opacity: 0.45;
    margin-top: 0.35rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent;
    border-bottom: 2px solid #1C1C1C;
    gap: 0;
    margin-bottom: 1.5rem;
}
.stTabs [data-baseweb="tab"] {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.77rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.4px !important;
    padding: 0.7rem 1.4rem !important;
    color: #999 !important;
    background: transparent !important;
    border: none !important;
    border-bottom: 3px solid transparent !important;
    margin-bottom: -2px !important;
}
.stTabs [aria-selected="true"] {
    color: #1C1C1C !important;
    border-bottom-color: #E8724A !important;
}

/* ── Section label ── */
.sec-label {
    font-family: 'Space Mono', monospace;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #999;
    margin: 1.5rem 0 0.8rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
}
.sec-label::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #D8D4CE;
}

/* ── Item cards ── */
.item-card {
    background: #fff;
    border: 1px solid #E0DDD7;
    border-radius: 3px;
    overflow: hidden;
    margin-bottom: 1rem;
    transition: transform 0.13s, box-shadow 0.13s;
}
.item-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(0,0,0,0.08);
}
.item-img-placeholder {
    width: 100%;
    height: 165px;
    background: #F2EFE9;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 3.5rem;
}
.item-body { padding: 0.9rem 1rem; }
.item-label {
    font-family: 'Space Mono', monospace;
    font-size: 0.9rem;
    font-weight: 700;
    color: #1C1C1C;
    margin-bottom: 0.3rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.item-cat-badge {
    display: inline-block;
    font-size: 0.7rem;
    font-weight: 600;
    padding: 0.18rem 0.55rem;
    border-radius: 2px;
    margin-bottom: 0.5rem;
}
.item-meta { font-size: 0.75rem; color: #888; margin-bottom: 0.25rem; }
.item-date {
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    color: #BBB;
    margin-top: 0.5rem;
}
.conf-wrap {
    background: #EEE;
    border-radius: 2px;
    height: 3px;
    margin-top: 0.4rem;
    overflow: hidden;
}
.conf-bar {
    height: 100%;
    background: #E8724A;
    border-radius: 2px;
}
.claimed-badge {
    background: #2ECC71;
    color: #fff;
    font-family: 'Space Mono', monospace;
    font-size: 0.6rem;
    font-weight: 700;
    padding: 0.18rem 0.45rem;
    border-radius: 2px;
    letter-spacing: 0.5px;
}

/* ── AI result box ── */
.ai-box {
    background: #1C1C1C;
    color: #F2EFE9;
    border-radius: 3px;
    padding: 1.1rem 1.3rem;
    margin: 0.8rem 0;
    border-left: 4px solid #E8724A;
    display: flex;
    align-items: flex-start;
    gap: 1rem;
}
.ai-label-text {
    font-family: 'Space Mono', monospace;
    font-size: 1rem;
    font-weight: 700;
}
.ai-sub { font-size: 0.75rem; opacity: 0.55; margin-top: 0.25rem; }

/* ── Buttons ── */
.stButton > button {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.77rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.4px !important;
    border-radius: 2px !important;
    border: 1.5px solid #1C1C1C !important;
    background: #1C1C1C !important;
    color: #F2EFE9 !important;
    padding: 0.55rem 1.3rem !important;
    transition: background 0.12s, border-color 0.12s !important;
    width: 100%;
}
.stButton > button:hover {
    background: #E8724A !important;
    border-color: #E8724A !important;
}
.btn-claim .stButton > button {
    background: #2ECC71 !important;
    border-color: #2ECC71 !important;
    font-size: 0.7rem !important;
    padding: 0.38rem 0.8rem !important;
}
.btn-claim .stButton > button:hover {
    background: #27AE60 !important;
    border-color: #27AE60 !important;
}

/* ── Inputs ── */
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stSelectbox > div > div {
    border-radius: 2px !important;
    border: 1.5px solid #DDD !important;
    font-family: 'DM Sans', sans-serif !important;
    background: #fff !important;
}
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: #E8724A !important;
    box-shadow: 0 0 0 2px rgba(232,114,74,0.15) !important;
}
label[data-testid="stWidgetLabel"] p {
    font-family: 'Space Mono', monospace !important;
    font-size: 0.75rem !important;
    font-weight: 700 !important;
    letter-spacing: 0.3px !important;
    color: #555 !important;
}

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 3.5rem 2rem;
    color: #999;
    background: #fff;
    border: 1px solid #E0DDD7;
    border-radius: 3px;
}
.empty-icon { font-size: 3.5rem; margin-bottom: 0.75rem; }
.empty-text {
    font-family: 'Space Mono', monospace;
    font-size: 0.9rem;
    color: #888;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; }
::-webkit-scrollbar-track { background: #F2EFE9; }
::-webkit-scrollbar-thumb { background: #CCC; border-radius: 3px; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  HERO
# ══════════════════════════════════════════════════════════════
counts = get_counts()
rate   = f"{int(counts['claimed']/counts['total']*100)}%" if counts['total'] else "–"

st.markdown(f"""
<div class="hero">
  <div>
    <div class="hero-title">📦 Fundkiste</div>
    <div class="hero-sub">Schulisches Fundbüro · KI-gestützte Objekterkennung</div>
  </div>
  <div class="hero-right">
    <div class="hero-pill">{counts['missing']} OFFEN</div>
    <div class="hero-meta">{counts['total']} GESAMT &nbsp;·&nbsp; {counts['claimed']} ABGEHOLT &nbsp;·&nbsp; {rate} QUOTE</div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Stat Cards ──
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
tab_search, tab_add, tab_stats = st.tabs([
    "🔍  Objekt suchen",
    "📷  Objekt melden",
    "📊  Statistiken",
])

# ─────────────────────────────────────────────────────────────
#  TAB: SUCHEN
# ─────────────────────────────────────────────────────────────
with tab_search:
    col_s, col_c = st.columns([3, 2])
    with col_s:
        q = st.text_input("", placeholder="🔍  Trinkflasche, Rucksack, Stift ...",
                          label_visibility="collapsed")
    with col_c:
        cat_filter = st.selectbox("", ["Alle"] + CATEGORIES,
                                  label_visibility="collapsed")

    show_claimed = st.checkbox("Bereits abgeholte Objekte anzeigen", value=False)

    # Filtern
    items = st.session_state["items"]
    if not show_claimed:
        items = [i for i in items if not i["is_claimed"]]
    if cat_filter != "Alle":
        items = [i for i in items if i["category"] == cat_filter]
    if q:
        items = [i for i in items if q.lower() in i["label"].lower()
                 or q.lower() in i.get("description","").lower()]

    # Sortierung: neueste zuerst
    items = list(reversed(items))

    st.markdown(
        f'<div class="sec-label">{len(items)} Objekte gefunden</div>',
        unsafe_allow_html=True
    )

    if not items:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">🔍</div>
            <div class="empty-text">Keine Objekte gefunden</div>
            <p style="margin-top:0.4rem;font-size:0.82rem;">Andere Suchbegriffe oder Kategorien versuchen</p>
        </div>""", unsafe_allow_html=True)
    else:
        cols = st.columns(3)
        for idx, item in enumerate(items):
            col = cols[idx % 3]
            with col:
                cat   = item["category"]
                icon  = CATEGORY_ICONS.get(cat, "📦")
                color = CATEGORY_COLORS.get(cat, "#888")
                conf  = int((item.get("confidence") or 0) * 100)
                loc   = item.get("location","")
                desc  = item.get("description","")
                claimed = item["is_claimed"]

                # Bild
                if item.get("image_bytes"):
                    img = Image.open(io.BytesIO(item["image_bytes"]))
                    img.thumbnail((600, 300))
                    st.image(img, use_container_width=True)
                else:
                    st.markdown(
                        f'<div class="item-img-placeholder">{icon}</div>',
                        unsafe_allow_html=True
                    )

                claimed_html = '<span class="claimed-badge">✓ ABGEHOLT</span>' if claimed else ""
                loc_html     = f'<div class="item-meta">📍 {loc}</div>' if loc else ""
                desc_html    = f'<p style="font-size:0.78rem;color:#666;margin:.3rem 0 0;">{desc[:80]}{"…" if len(desc)>80 else ""}</p>' if desc else ""
                conf_html    = f"""
                <div style="margin-top:0.45rem;">
                  <span style="font-size:0.68rem;color:#AAA;font-family:'Space Mono',monospace;">KI {conf}%</span>
                  <div class="conf-wrap"><div class="conf-bar" style="width:{conf}%"></div></div>
                </div>""" if conf > 0 else ""

                st.markdown(f"""
                <div class="item-card">
                  <div class="item-body">
                    <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:0.3rem;">
                      <div class="item-label">{item['label']}</div>
                      {claimed_html}
                    </div>
                    <span class="item-cat-badge" style="background:{color}22;color:{color};">{icon} {cat}</span>
                    {loc_html}
                    {desc_html}
                    {conf_html}
                    <div class="item-date">Gemeldet: {item['created_at']}</div>
                  </div>
                </div>""", unsafe_allow_html=True)

                if not claimed:
                    st.markdown('<div class="btn-claim">', unsafe_allow_html=True)
                    if st.button("✓ Als abgeholt markieren", key=f"claim_{item['id']}"):
                        claim_item(item["id"])
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  TAB: MELDEN
# ─────────────────────────────────────────────────────────────
with tab_add:
    left, right = st.columns([1, 1], gap="large")

    with left:
        st.markdown('<div class="sec-label">Foto</div>', unsafe_allow_html=True)
        upload_tab, cam_tab = st.tabs(["📁 Datei", "📷 Kamera"])

        raw = None
        with upload_tab:
            raw = st.file_uploader("", type=["jpg","jpeg","png"],
                                   label_visibility="collapsed")
        with cam_tab:
            cam = st.camera_input("", label_visibility="collapsed")
            if cam:
                raw = cam

        pil_img    = None
        ai_result  = None

        if raw:
            pil_img = Image.open(raw)
            st.image(pil_img, use_container_width=True)

            with st.spinner("🤖 KI analysiert …"):
                ai_result = detect(pil_img)

            conf_pct = int((ai_result["confidence"] or 0) * 100)
            dev_lbl  = ai_result.get("device","cpu")
            dev_icon = "⚡ GPU" if "cuda" in str(dev_lbl) else "🖥️ CPU"

            if ai_result["success"]:
                st.markdown(f"""
                <div class="ai-box">
                  <div style="font-size:2rem;line-height:1">🤖</div>
                  <div>
                    <div class="ai-label-text">{ai_result['label']}</div>
                    <div class="ai-sub">
                      {ai_result['category']} &nbsp;·&nbsp;
                      Konfidenz: {conf_pct}% &nbsp;·&nbsp; {dev_icon}
                    </div>
                    <div class="conf-wrap" style="width:180px;margin-top:0.5rem;">
                      <div class="conf-bar" style="width:{conf_pct}%"></div>
                    </div>
                  </div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="ai-box" style="border-left-color:#888;">
                  <div style="font-size:2rem">🤔</div>
                  <div>
                    <div class="ai-label-text">Kein Objekt erkannt</div>
                    <div class="ai-sub">Bitte Bezeichnung manuell eingeben</div>
                  </div>
                </div>""", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="sec-label">Objektdaten</div>', unsafe_allow_html=True)

        default_label = ai_result["label"] if ai_result and ai_result["success"] else ""
        default_cat   = ai_result["category"] if ai_result and ai_result["success"] else "Sonstiges"
        default_conf  = ai_result["confidence"] if ai_result else 0.0

        label = st.text_input("Bezeichnung *", value=default_label,
                              placeholder="z.B. Blaue Trinkflasche")

        cat_idx = CATEGORIES.index(default_cat) if default_cat in CATEGORIES else len(CATEGORIES)-1
        category = st.selectbox("Kategorie *", CATEGORIES, index=cat_idx)

        location = st.text_input("Fundort",
                                 placeholder="z.B. Raum 204, Sporthalle, Schulhof …")

        description = st.text_area("Beschreibung",
                                   placeholder="Farbe, Aufschriften, Besonderheiten …",
                                   height=95)

        st.markdown("<div style='height:0.3rem'></div>", unsafe_allow_html=True)

        if st.button("📦 Zur Fundkiste hinzufügen", use_container_width=True):
            if not label.strip():
                st.error("Bitte eine Bezeichnung eingeben.")
            else:
                img_bytes = raw.getvalue() if raw else None
                add_item(
                    label=label.strip(),
                    category=category,
                    location=location.strip(),
                    description=description.strip(),
                    image_bytes=img_bytes,
                    confidence=default_conf,
                )
                st.success(f"✅ '{label}' wurde zur Fundkiste hinzugefügt!")
                st.balloons()

        # Hinweis Session State
        st.markdown("""
        <div style="background:#FFF8F5;border:1px solid #F5C9B3;border-radius:3px;
                    padding:0.75rem 1rem;margin-top:1rem;font-size:0.78rem;color:#C0632A;">
          <b>Hinweis:</b> Daten werden nur für diese Browser-Session gespeichert.
          Nach dem Schließen des Tabs sind sie weg.
        </div>""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────
#  TAB: STATISTIKEN
# ─────────────────────────────────────────────────────────────
with tab_stats:
    all_items = st.session_state["items"]

    if not all_items:
        st.markdown("""
        <div class="empty-state">
            <div class="empty-icon">📊</div>
            <div class="empty-text">Noch keine Daten</div>
            <p style="margin-top:0.4rem;font-size:0.82rem;">Melde erst ein Objekt, um Statistiken zu sehen</p>
        </div>""", unsafe_allow_html=True)
    else:
        # Statistik pro Kategorie berechnen
        stats = {}
        for cat in CATEGORIES:
            stats[cat] = {"total": 0, "missing": 0, "claimed": 0}
        for item in all_items:
            cat = item["category"]
            if cat not in stats:
                stats[cat] = {"total": 0, "missing": 0, "claimed": 0}
            stats[cat]["total"] += 1
            if item["is_claimed"]:
                stats[cat]["claimed"] += 1
            else:
                stats[cat]["missing"] += 1

        active = {k: v for k, v in stats.items() if v["total"] > 0}
        df = pd.DataFrame([
            {"Kategorie": k, **v} for k, v in active.items()
        ]).sort_values("total", ascending=False)

        st.markdown('<div class="sec-label">Verluste nach Kategorie</div>', unsafe_allow_html=True)

        col_bar, col_donut = st.columns([3, 2])

        with col_bar:
            colors = [CATEGORY_COLORS.get(c, "#888") for c in df["Kategorie"]]
            fig = go.Figure()
            fig.add_trace(go.Bar(
                y=df["Kategorie"], x=df["missing"],
                name="Noch offen", orientation="h",
                marker=dict(color=colors, line=dict(width=0)),
            ))
            fig.add_trace(go.Bar(
                y=df["Kategorie"], x=df["claimed"],
                name="Abgeholt", orientation="h",
                marker=dict(color="rgba(0,0,0,0.1)", line=dict(width=0)),
            ))
            fig.update_layout(
                barmode="stack",
                plot_bgcolor="white", paper_bgcolor="white",
                font=dict(family="DM Sans", size=12, color="#1C1C1C"),
                margin=dict(l=5, r=5, t=5, b=5),
                legend=dict(
                    orientation="h", y=1.06, x=1, xanchor="right",
                    font=dict(family="Space Mono", size=10),
                ),
                xaxis=dict(showgrid=True, gridcolor="#F2EFE9", zeroline=False),
                yaxis=dict(showgrid=False),
                height=max(220, len(active) * 42),
            )
            st.plotly_chart(fig, use_container_width=True)

        with col_donut:
            fig2 = go.Figure(go.Pie(
                labels=df["Kategorie"],
                values=df["total"],
                hole=0.58,
                marker=dict(
                    colors=[CATEGORY_COLORS.get(c, "#888") for c in df["Kategorie"]],
                    line=dict(color="white", width=2),
                ),
                textinfo="none",
                hovertemplate="<b>%{label}</b><br>%{value} Objekte<extra></extra>",
            ))
            total_all = df["total"].sum()
            fig2.update_layout(
                plot_bgcolor="white", paper_bgcolor="white",
                font=dict(family="DM Sans", size=11),
                margin=dict(l=5, r=5, t=5, b=5),
                showlegend=False,
                height=max(220, len(active) * 42),
                annotations=[dict(
                    text=f"<b>{total_all}</b><br><span style='font-size:11px'>Objekte</span>",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=20, family="Space Mono", color="#1C1C1C"),
                )],
            )
            st.plotly_chart(fig2, use_container_width=True)

        # Detail-Tabelle
        st.markdown('<div class="sec-label">Detailübersicht</div>', unsafe_allow_html=True)
        for _, row in df.iterrows():
            cat   = row["Kategorie"]
            icon  = CATEGORY_ICONS.get(cat, "📦")
            color = CATEGORY_COLORS.get(cat, "#888")
            total = int(row["total"])
            miss  = int(row["missing"])
            clmd  = int(row["claimed"])
            pct   = int(clmd / total * 100) if total else 0

            st.markdown(f"""
            <div style="background:#fff;border:1px solid #E0DDD7;border-radius:3px;
                        padding:0.85rem 1.1rem;margin-bottom:0.45rem;
                        display:flex;align-items:center;gap:1rem;">
              <span style="font-size:1.4rem;width:1.8rem;text-align:center">{icon}</span>
              <div style="flex:1;">
                <div style="font-family:'Space Mono',monospace;font-size:0.82rem;
                            font-weight:700;">{cat}</div>
                <div style="height:5px;background:#F2EFE9;border-radius:2px;
                            margin-top:0.35rem;overflow:hidden;">
                  <div style="height:100%;width:{pct}%;background:{color};border-radius:2px;"></div>
                </div>
              </div>
              <div style="text-align:right;font-family:'Space Mono',monospace;font-size:0.78rem;min-width:80px">
                <span style="color:{color};font-weight:700;">{miss} offen</span>
                <span style="color:#CCC"> / {total}</span>
                <div style="font-size:0.65rem;color:#AAA;margin-top:0.1rem">{pct}% abgeholt</div>
              </div>
            </div>""", unsafe_allow_html=True)

        # Highlight: häufigster Verlust
        if not df.empty:
            top = df.iloc[0]
            top_cat   = top["Kategorie"]
            top_icon  = CATEGORY_ICONS.get(top_cat, "📦")
            top_miss  = int(top["missing"])
            st.markdown(f"""
            <div style="background:#1C1C1C;color:#F2EFE9;border-radius:3px;
                        padding:1.1rem 1.4rem;margin-top:1.2rem;
                        border-left:4px solid #E8724A;">
              <div style="font-family:'Space Mono',monospace;font-size:0.68rem;
                          opacity:0.5;letter-spacing:1.5px;text-transform:uppercase;">
                Häufigster Verlust
              </div>
              <div style="font-family:'Space Mono',monospace;font-size:1.1rem;
                          font-weight:700;margin-top:0.3rem;">
                {top_icon} {top_cat} &nbsp;·&nbsp; {top_miss} offen
              </div>
            </div>""", unsafe_allow_html=True)

        # Hinweis Session State
        st.markdown("""
        <div style="background:#F9F9F9;border:1px solid #E0DDD7;border-radius:3px;
                    padding:0.75rem 1rem;margin-top:1.2rem;font-size:0.78rem;color:#888;">
          Statistiken beziehen sich auf die aktuelle Browser-Session.
        </div>""", unsafe_allow_html=True)