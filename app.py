import io
import os
import time
import random
import math
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image, ImageDraw, ImageFilter

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


# =========================
# Branding (change later)
# =========================
BRAND_NAME = "WeaveScope"
TAGLINE = "AI-assisted detection of textile pattern misuse across marketplaces"
ASSETS_DIR = "assets"  # put your logo later: assets/logo.png


# =========================
# Page setup
# =========================
st.set_page_config(
    page_title=BRAND_NAME,
    page_icon="🧵",
    layout="wide",
)

# =========================
# CSS (make Streamlit look like a real website)
# =========================
st.markdown(
    """
<style>
/* Global spacing */
.block-container { padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1200px; }

/* Hide Streamlit chrome */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Top bar */
.topbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 16px; border: 1px solid #E6E8EF; border-radius: 16px;
  background: #FFFFFF;
}
.brand-left { display: flex; gap: 14px; align-items: center; }
.logo-slot {
  width: 48px; height: 48px; border-radius: 12px;
  border: 1.5px dashed #B8C0D4; display: flex; align-items: center; justify-content: center;
  color: #64748B; font-weight: 600; background: #F8FAFF;
  overflow: hidden;
}
.brand-title { font-size: 16px; font-weight: 800; color: #0F172A; line-height: 1.1; }
.brand-sub { font-size: 12px; color: #475569; margin-top: 2px; }
.top-actions { display: flex; gap: 10px; align-items: center; }
.pill {
  padding: 8px 10px; border: 1px solid #E6E8EF; border-radius: 999px;
  font-size: 12px; color: #0F172A; background: #F8FAFF;
}

/* Hero */
.hero {
  margin-top: 16px;
  padding: 20px 18px;
  border-radius: 18px;
  border: 1px solid #E6E8EF;
  background: linear-gradient(135deg, #F8FAFF 0%, #FFFFFF 45%, #F3F7FF 100%);
}
.hero h1 { font-size: 28px; margin: 0; color: #0F172A; }
.hero p { margin-top: 8px; margin-bottom: 0; color: #334155; font-size: 14px; line-height: 1.5; }
.hero-grid {
  margin-top: 14px;
  display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px;
}
.kpi {
  padding: 12px; border-radius: 14px; border: 1px solid #E6E8EF; background: #FFFFFF;
}
.kpi .k { font-size: 12px; color: #64748B; }
.kpi .v { font-size: 18px; font-weight: 800; color: #0F172A; margin-top: 4px; }
.kpi .s { font-size: 12px; color: #334155; margin-top: 6px; }

/* Cards */
.card {
  border: 1px solid #E6E8EF; border-radius: 18px; background: #FFFFFF; padding: 14px;
}
.card-title { font-size: 14px; font-weight: 800; color: #0F172A; margin-bottom: 8px; }
.muted { color: #64748B; font-size: 12px; }
.hr { height: 1px; background: #E6E8EF; margin: 10px 0; }

/* Badges */
.badge {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 6px 10px; border-radius: 999px; font-weight: 700; font-size: 12px;
  border: 1px solid #E6E8EF; background: #F8FAFF; color: #0F172A;
}
.badge-high { background: #FFF1F2; border-color: #FECACA; color: #991B1B; }
.badge-med  { background: #FFFBEB; border-color: #FDE68A; color: #92400E; }
.badge-low  { background: #F0FDF4; border-color: #BBF7D0; color: #166534; }

/* Product tiles */
.tile {
  border: 1px solid #E6E8EF; border-radius: 16px; background: #FFFFFF; padding: 10px;
}
.tile h4 { margin: 8px 0 2px 0; font-size: 13px; color: #0F172A; }
.tile p { margin: 0; font-size: 12px; color: #475569; }
.small { font-size: 12px; color: #334155; }

/* Footer note */
.footer-note {
  margin-top: 18px; padding: 12px 14px;
  border: 1px solid #E6E8EF; border-radius: 14px; background: #FFFFFF;
  color: #475569; font-size: 12px;
}
</style>
""",
    unsafe_allow_html=True
)


# =========================
# Utilities
# =========================
def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def stable_seed_from_bytes(b: bytes) -> int:
    if not b:
        return random.randint(0, 10**9)
    return int.from_bytes(b[:8], "little", signed=False)


def load_logo_if_exists():
    path = os.path.join(ASSETS_DIR, "logo.png")
    if os.path.exists(path):
        try:
            return Image.open(path).convert("RGBA")
        except:
            return None
    return None


# =========================
# Textile swatch generator (no random geometric shapes)
# =========================
def textile_swatch(seed: int, size=(520, 520), style=None) -> Image.Image:
    rng = random.Random(seed)
    w, h = size
    style = style or rng.choice(["weave", "plaid", "herringbone", "stripes", "ikat_soft"])

    # palettes (textile-ish)
    palettes = [
        [(15, 23, 42), (37, 99, 235), (248, 250, 255), (99, 102, 241)],
        [(17, 94, 89), (240, 253, 250), (6, 78, 59), (20, 184, 166)],
        [(120, 53, 15), (255, 247, 237), (234, 88, 12), (30, 41, 59)],
        [(88, 28, 135), (250, 245, 255), (168, 85, 247), (15, 23, 42)],
        [(30, 41, 59), (241, 245, 249), (100, 116, 139), (226, 232, 240)]
    ]
    base = rng.choice(palettes)
    c0, c1, c2, c3 = base

    img = Image.new("RGB", (w, h), c2)
    d = ImageDraw.Draw(img)

    # subtle noise texture
    noise = np.random.default_rng(seed).integers(0, 18, size=(h, w, 1), dtype=np.uint8)
    noise_img = Image.fromarray(np.repeat(noise, 3, axis=2), "RGB")
    img = Image.blend(img, noise_img, 0.10)
    d = ImageDraw.Draw(img)

    if style == "weave":
        # warp/weft threads
        step = rng.choice([6, 8, 10])
        for x in range(0, w, step):
            col = c1 if (x // step) % 2 == 0 else c3
            d.line([(x, 0), (x, h)], fill=col, width=1)
        for y in range(0, h, step):
            col = c0 if (y // step) % 2 == 0 else c3
            d.line([(0, y), (w, y)], fill=col, width=1)

        img = img.filter(ImageFilter.GaussianBlur(radius=0.4))

    elif style == "stripes":
        stripe = rng.choice([18, 24, 32])
        for i, x in enumerate(range(0, w, stripe)):
            col = [c0, c1, c3, c2][i % 4]
            d.rectangle([x, 0, min(w, x + stripe - 2), h], fill=col)
        img = img.filter(ImageFilter.GaussianBlur(radius=0.6))

    elif style == "plaid":
        step = rng.choice([22, 28, 34])
        for x in range(0, w, step):
            col = c1 if (x // step) % 2 == 0 else c3
            d.rectangle([x, 0, min(w, x + 6), h], fill=col)
        for y in range(0, h, step):
            col = c0 if (y // step) % 2 == 0 else c3
            d.rectangle([0, y, w, min(h, y + 6)], fill=col)
        # thin accents
        for x in range(0, w, step // 2):
            d.line([(x, 0), (x, h)], fill=(255, 255, 255), width=1)
        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))

    elif style == "herringbone":
        # diagonal micro pattern
        step = rng.choice([14, 16, 18])
        for y in range(0, h, step):
            for x in range(0, w, step):
                col = c1 if ((x // step + y // step) % 2 == 0) else c0
                d.polygon([(x, y), (x + step, y + step//2), (x, y + step)], fill=col)
                d.polygon([(x + step, y), (x + step, y + step), (x, y + step//2)], fill=c3)
        img = img.filter(ImageFilter.GaussianBlur(radius=0.6))

    elif style == "ikat_soft":
        # soft blurred bands
        band = rng.choice([40, 56, 72])
        for x in range(0, w, band):
            col = c1 if (x // band) % 2 == 0 else c0
            d.rectangle([x, 0, min(w, x + band), h], fill=col)
        img = img.filter(ImageFilter.GaussianBlur(radius=3.2))
        # add soft noise again
        noise2 = np.random.default_rng(seed + 9).integers(0, 20, size=(h, w, 1), dtype=np.uint8)
        noise2_img = Image.fromarray(np.repeat(noise2, 3, axis=2), "RGB")
        img = Image.blend(img, noise2_img, 0.08)

    # vignette
    vign = Image.new("L", (w, h), 0)
    vd = ImageDraw.Draw(vign)
    vd.ellipse([-w*0.2, -h*0.2, w*1.2, h*1.2], fill=255)
    vign = vign.filter(ImageFilter.GaussianBlur(radius=50))
    img = Image.composite(img, Image.new("RGB", (w, h), (255, 255, 255)), vign)

    return img


def ai_highlight_overlay(img: Image.Image, seed: int) -> Image.Image:
    """Simulate AI 'attention map' on textile pattern (subtle + marketing)."""
    rng = random.Random(seed)
    base = img.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    w, h = base.size
    for _ in range(rng.randint(3, 6)):
        x0 = rng.randint(0, int(w * 0.55))
        y0 = rng.randint(0, int(h * 0.55))
        x1 = x0 + rng.randint(int(w * 0.20), int(w * 0.50))
        y1 = y0 + rng.randint(int(h * 0.20), int(h * 0.50))
        # blue-ish highlight
        d.rounded_rectangle([x0, y0, x1, y1], radius=22, outline=(37, 99, 235, 230), width=6)
        d.rounded_rectangle([x0+6, y0+6, x1-6, y1-6], radius=18, fill=(37, 99, 235, 35))

    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=1.2))
    return Image.alpha_composite(base, overlay).convert("RGB")


def risk_level(score: float) -> str:
    if score >= 70:
        return "high"
    if score >= 35:
        return "med"
    return "low"


def make_pdf_report(brand: str, query_img: Image.Image, meta: dict, matches: list) -> bytes:
    buff = io.BytesIO()
    c = canvas.Canvas(buff, pagesize=A4)
    W, H = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, H - 42, f"{brand} — Pattern Risk Assessment")
    c.setFont("Helvetica", 9)
    c.drawString(40, H - 58, f"Generated: {now_str()}")

    # Query image
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, H - 90, "Submitted textile pattern")
    img_buf = io.BytesIO()
    query_img.resize((220, 220)).save(img_buf, format="PNG")
    img_buf.seek(0)
    c.drawImage(ImageReader(img_buf), 40, H - 330, width=220, height=220, mask="auto")

    # Meta
    c.setFont("Helvetica", 9)
    x = 280
    y = H - 105
    lines = [
        f"Culture / Community: {meta.get('culture','—')}",
        f"Geographic origin: {meta.get('origin','—')}",
        f"Meaning / function: {meta.get('meaning','—')}",
        f"Sensitivity: {meta.get('sensitivity','—')}",
        f"Consent: {meta.get('consent','—')}",
    ]
    for i, ln in enumerate(lines):
        c.drawString(x, y - 16*i, ln)

    # Matches
    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, H - 370, "Top matches (evidence)")
    y = H - 390
    c.setFont("Helvetica", 9)

    for idx, m in enumerate(matches[:3], start=1):
        if y < 120:
            c.showPage()
            y = H - 60
        c.setFont("Helvetica-Bold", 9)
        c.drawString(40, y, f"{idx}. {m['title']} — Risk {m['score']}/100")
        c.setFont("Helvetica", 8)
        c.drawString(40, y - 12, f"Brand: {m['brand']} | Source: {m['source']}")
        c.drawString(40, y - 24, f"URL: {m['url']}")
        c.drawString(40, y - 36, f"Visual similarity: {m['similarity']}% | Attribution signal: {m['attribution']}")
        if m["flags"]:
            c.drawString(40, y - 48, f"Language flags: {', '.join(m['flags'])}")
        y -= 70

    c.setFont("Helvetica-Oblique", 8)
    c.drawString(
        40,
        50,
        "Note: This output is an advisory risk signal to support community review. It is not a legal determination."
    )
    c.save()
    buff.seek(0)
    return buff.read()


# =========================
# Session state
# =========================
if "registry" not in st.session_state:
    st.session_state.registry = []
if "scan" not in st.session_state:
    st.session_state.scan = None
if "alerts" not in st.session_state:
    st.session_state.alerts = []


# =========================
# Topbar
# =========================
logo_img = load_logo_if_exists()

logo_html = "LOGO"
if logo_img:
    # render logo inside the slot (base64 not needed; streamlit can show image)
    # We'll show the logo image in a column near the slot.
    pass

left, right = st.columns([0.78, 0.22], gap="small")

with left:
    st.markdown('<div class="topbar">', unsafe_allow_html=True)
    cA, cB = st.columns([0.12, 0.88], gap="small")
    with cA:
        if logo_img:
            st.image(logo_img, width=48)
        else:
            st.markdown('<div class="logo-slot">LOGO</div>', unsafe_allow_html=True)
    with cB:
        st.markdown(
            f"""
            <div>
              <div class="brand-title">{BRAND_NAME}</div>
              <div class="brand-sub">{TAGLINE}</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown('<div class="topbar">', unsafe_allow_html=True)
    st.markdown('<div class="top-actions">', unsafe_allow_html=True)
    st.markdown(f'<div class="pill">Live monitoring</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="pill">{now_str()}</div>', unsafe_allow_html=True)
    st.markdown("</div></div>", unsafe_allow_html=True)


# =========================
# Hero section
# =========================
st.markdown(
    f"""
<div class="hero">
  <h1>Detect textile pattern reuse at scale — with AI support</h1>
  <p>
    Upload a textile pattern and instantly surface similar items across marketplaces, with risk signals,
    evidence links, and an explainable breakdown designed for community review and brand dialogue.
  </p>
  <div class="hero-grid">
    <div class="kpi"><div class="k">Visual match ranking</div><div class="v">Top-K</div><div class="s">Similarity + structure cues</div></div>
    <div class="kpi"><div class="k">Context signals</div><div class="v">NLP</div><div class="s">Attribution & wording checks</div></div>
    <div class="kpi"><div class="k">Explainable score</div><div class="v">0–100</div><div class="s">Factor contributions shown</div></div>
    <div class="kpi"><div class="k">Evidence export</div><div class="v">PDF</div><div class="s">Timestamp + source URLs</div></div>
  </div>
</div>
""",
    unsafe_allow_html=True
)

st.write("")

tabs = st.tabs(["Search", "Monitoring", "Registry", "Reports"])


# =========================
# Tab: Search
# =========================
with tabs[0]:
    left, right = st.columns([0.58, 0.42], gap="large")

    with left:
        st.markdown('<div class="card"><div class="card-title">Submit a textile pattern</div>', unsafe_allow_html=True)

        uploaded = st.file_uploader(
            "Pattern image (fabric, motif, embroidery, print)",
            type=["png", "jpg", "jpeg"],
            label_visibility="visible"
        )

        c1, c2 = st.columns(2)
        with c1:
            culture = st.text_input("Culture / community", placeholder="e.g., community name")
            origin = st.text_input("Geographic origin", placeholder="e.g., region / country")
        with c2:
            sensitivity = st.selectbox("Sensitivity level", ["Everyday", "Ceremonial", "Sacred"], index=0)
            consent = st.selectbox("Consent", ["Private", "Community shared", "Monitoring enabled"], index=1)

        meaning = st.text_area("Meaning / function (optional)", placeholder="Short context about meaning, function, usage…")

        c3, c4 = st.columns(2)
        with c3:
            marketplaces = st.multiselect(
                "Marketplaces",
                ["CatalogX", "DemoMarket", "CraftHub"],
                default=["CatalogX", "DemoMarket"]
            )
        with c4:
            top_k = st.slider("Results", 3, 12, 6)

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

        c5, c6 = st.columns([0.62, 0.38], gap="small")
        with c5:
            run = st.button("✨ Analyze with AI", use_container_width=True)
        with c6:
            sample = st.button("Use a sample textile swatch", use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="card"><div class="card-title">Preview</div>', unsafe_allow_html=True)

        if sample and not uploaded:
            seed = random.randint(10_000, 99_999)
            query_img = textile_swatch(seed, style=random.choice(["weave", "plaid", "herringbone", "stripes", "ikat_soft"]))
            qbytes = io.BytesIO()
            query_img.save(qbytes, format="PNG")
            uploaded = type("X", (), {"getvalue": lambda: qbytes.getvalue()})()

        if uploaded:
            img_bytes = uploaded.getvalue()
            query_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            seed = stable_seed_from_bytes(img_bytes)
        else:
            # neutral textile placeholder (looks like fabric)
            seed = 424242
            query_img = textile_swatch(seed, style="weave")

        st.image(query_img, use_column_width=True)

        st.markdown(
            """
            <div class="muted">
              Tip: textile photos work best — close-up fabric, embroidery, woven motifs, or printed patterns.
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("</div>", unsafe_allow_html=True)

    if run:
        meta = {
            "culture": culture or "—",
            "origin": origin or "—",
            "meaning": (meaning[:180] + "…") if len(meaning) > 180 else (meaning or "—"),
            "sensitivity": sensitivity,
            "consent": consent,
            "marketplaces": ", ".join(marketplaces) if marketplaces else "—",
            "created_at": now_str()
        }

        # Simulated AI pipeline UI (marketing feel)
        with st.status("AI pipeline running", expanded=True) as status:
            st.write("Preprocessing image (normalization, denoise)")
            time.sleep(0.25)
            st.write("Extracting pattern signature (multi-scale features)")
            time.sleep(0.25)
            st.write("Building visual embedding & scanning vector index")
            time.sleep(0.25)
            st.write("Reading product narratives for attribution & wording signals")
            time.sleep(0.25)
            st.write("Generating explainable risk score + evidence pack")
            time.sleep(0.25)
            status.update(label="Analysis complete", state="complete", expanded=False)

        # Create “AI highlights”
        highlighted = ai_highlight_overlay(query_img, seed)

        # Fake matches (textile swatches that look realistic)
        titles = [
            "Woven Jacquard Jacket", "Printed Scarf (Limited Run)", "Decor Textile Cushion",
            "Embroidery Panel Bag", "Patterned Wrap Dress", "Home Textile Wall Hanging",
            "Cotton Kimono Robe", "Handmade Tote with Motif"
        ]
        brands = ["Maison Lume", "Studio Loom", "North & Co", "Atelier Vale", "Kora Works", "Urban Nomad"]
        sources = ["CatalogX", "DemoMarket", "CraftHub"]

        def pick_flags(rng):
            flags_pool = ["tribal", "exotic", "ethnic", "primitive", "oriental-inspired"]
            flags = []
            if rng.random() < 0.45:
                flags.append(rng.choice(flags_pool))
            return flags

        rows = []
        rng = random.Random(seed)
        for i in range(top_k):
            sim = rng.uniform(62, 92)  # percent
            score = (
                0.48 * sim
                + (25 if sensitivity == "Sacred" else 15 if sensitivity == "Ceremonial" else 6)
                + (12 if rng.random() < 0.6 else 4)
            )
            score = max(0, min(100, score))
            lvl = risk_level(score)

            sw = textile_swatch(seed + i*91 + 7, style=rng.choice(["weave", "plaid", "herringbone", "stripes", "ikat_soft"]))
            attribution = "present" if rng.random() < 0.35 else "absent"
            flags = pick_flags(rng)
            url = f"https://{rng.choice(sources).lower()}.example.com/listing/{seed%9999}-{i}"

            rows.append({
                "rank": i + 1,
                "title": rng.choice(titles),
                "brand": rng.choice(brands),
                "source": rng.choice(sources),
                "similarity": int(sim),
                "score": round(score, 1),
                "level": lvl,
                "attribution": attribution,
                "flags": flags,
                "img": sw,
                "url": url
            })

        rows = sorted(rows, key=lambda r: (r["score"], r["similarity"]), reverse=True)

        # Persist scan
        st.session_state.scan = {
            "meta": meta,
            "query_img": query_img,
            "highlighted": highlighted,
            "rows": rows,
            "scan_id": f"WS-{random.randint(10000,99999)}"
        }

        # Registry add
        st.session_state.registry.insert(0, {
            "id": f"ITEM-{len(st.session_state.registry)+1:03d}",
            "culture": meta["culture"],
            "origin": meta["origin"],
            "sensitivity": meta["sensitivity"],
            "consent": meta["consent"],
            "created_at": meta["created_at"],
        })

        # Alerts (if monitoring enabled)
        if consent == "Monitoring enabled":
            for r in rows[:3]:
                if r["score"] >= 70:
                    st.session_state.alerts.insert(0, {
                        "created_at": now_str(),
                        "title": r["title"],
                        "brand": r["brand"],
                        "risk": r["score"],
                        "similarity": r["similarity"],
                        "status": "New",
                        "url": r["url"]
                    })

        st.success("Results ready. Scroll down to review insights and matches.")

        # Results panel (same page for “website” feel)
        st.write("")
        st.markdown('<div class="card"><div class="card-title">AI insights</div>', unsafe_allow_html=True)
        cA, cB = st.columns([1, 1], gap="large")
        with cA:
            st.markdown('<div class="muted">Pattern attention & salient regions</div>', unsafe_allow_html=True)
            st.image(highlighted, use_column_width=True)
        with cB:
            top = rows[0]
            badge_class = "badge-high" if top["level"] == "high" else "badge-med" if top["level"] == "med" else "badge-low"
            badge_label = "High risk" if top["level"] == "high" else "Medium risk" if top["level"] == "med" else "Low risk"

            st.markdown(
                f'<div class="badge {badge_class}">● {badge_label} — {top["score"]}/100</div>',
                unsafe_allow_html=True
            )
            st.write("")
            st.markdown("**Key drivers**")
            drivers = []
            if sensitivity in ["Ceremonial", "Sacred"]:
                drivers.append(f"Sensitivity level: **{sensitivity}**")
            if top["attribution"] == "absent":
                drivers.append("No attribution detected in narrative")
            if top["flags"]:
                drivers.append(f"Flagged wording: **{', '.join(top['flags'])}**")
            drivers.append(f"Visual similarity: **{top['similarity']}%**")
            for dline in drivers[:5]:
                st.write(f"• {dline}")

            st.write("")
            st.markdown("**Pattern signature** (simulated)")
            sig = np.clip(np.random.default_rng(seed).normal(0.55, 0.18, 16), 0, 1)
            st.bar_chart(sig)

        st.markdown("</div>", unsafe_allow_html=True)

        st.write("")
        st.markdown('<div class="card"><div class="card-title">Top matches across marketplaces</div>', unsafe_allow_html=True)

        cols = st.columns(3, gap="large")
        for i, r in enumerate(rows[:6]):
            with cols[i % 3]:
                st.markdown('<div class="tile">', unsafe_allow_html=True)
                st.image(r["img"], use_column_width=True)
                st.markdown(f"<h4>{r['title']}</h4>", unsafe_allow_html=True)
                st.markdown(f"<p>{r['brand']} • {r['source']}</p>", unsafe_allow_html=True)

                badge_class = "badge-high" if r["level"] == "high" else "badge-med" if r["level"] == "med" else "badge-low"
                badge_label = "High" if r["level"] == "high" else "Medium" if r["level"] == "med" else "Low"
                st.markdown(
                    f'<div class="badge {badge_class}">Risk {badge_label} • {r["score"]}/100</div>',
                    unsafe_allow_html=True
                )
                st.caption(r["url"])

                st.progress(r["similarity"])
                st.markdown(
                    f"<div class='small'>Similarity: <b>{r['similarity']}%</b> • Attribution: <b>{r['attribution']}</b></div>",
                    unsafe_allow_html=True
                )
                if r["flags"]:
                    st.markdown(f"<div class='small'>Language signals: <b>{', '.join(r['flags'])}</b></div>", unsafe_allow_html=True)

                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # PDF export
        st.write("")
        pdf = make_pdf_report(BRAND_NAME, query_img, meta, rows)
        st.download_button(
            "Download evidence report (PDF)",
            data=pdf,
            file_name=f"{BRAND_NAME}_Report_{st.session_state.scan['scan_id']}.pdf",
            mime="application/pdf",
            use_container_width=True
        )


# =========================
# Tab: Monitoring
# =========================
with tabs[1]:
    st.markdown('<div class="card"><div class="card-title">Monitoring & alerts</div>', unsafe_allow_html=True)
    st.markdown(
        "<div class='muted'>New listings are surfaced when similarity and context signals exceed the alert threshold.</div>",
        unsafe_allow_html=True
    )
    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

    if not st.session_state.alerts:
        st.info("No active alerts at the moment.")
    else:
        for idx, a in enumerate(st.session_state.alerts[:8]):
            c1, c2, c3, c4 = st.columns([2.1, 0.8, 0.9, 1.0], gap="small")
            with c1:
                st.markdown(f"**{a['title']}**  \n{a['brand']}")
                st.caption(a["url"])
                st.caption(f"Detected: {a['created_at']}")
            with c2:
                st.metric("Risk", f"{a['risk']}/100")
            with c3:
                st.metric("Similarity", f"{a['similarity']}%")
            with c4:
                st.write("Status")
                new_status = st.selectbox(
                    " ",
                    ["New", "In review", "Ignored", "Flagged"],
                    index=["New", "In review", "Ignored", "Flagged"].index(a["status"]) if a["status"] in ["New","In review","Ignored","Flagged"] else 0,
                    key=f"st_{idx}"
                )
                st.session_state.alerts[idx]["status"] = new_status

    st.markdown("</div>", unsafe_allow_html=True)


# =========================
# Tab: Registry
# =========================
with tabs[2]:
    st.markdown('<div class="card"><div class="card-title">Cultural registry</div>', unsafe_allow_html=True)
    st.markdown("<div class='muted'>Submitted items and consent settings.</div>", unsafe_allow_html=True)
    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

    if not st.session_state.registry:
        st.info("Registry is empty.")
    else:
        df = pd.DataFrame(st.session_state.registry)
        st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("</div>", unsafe_allow_html=True)


# =========================
# Tab: Reports
# =========================
with tabs[3]:
    st.markdown('<div class="card"><div class="card-title">Reports</div>', unsafe_allow_html=True)
    st.markdown("<div class='muted'>Generate and share evidence packages with timestamps and source links.</div>", unsafe_allow_html=True)
    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

    if not st.session_state.scan:
        st.info("Run an analysis first to generate a report.")
    else:
        scan = st.session_state.scan
        st.write(f"Latest scan: **{scan['scan_id']}**")
        st.caption(f"Created: {scan['meta']['created_at']} • Marketplaces: {scan['meta']['marketplaces']}")

        pdf = make_pdf_report(BRAND_NAME, scan["query_img"], scan["meta"], scan["rows"])
        st.download_button(
            "Download latest report (PDF)",
            data=pdf,
            file_name=f"{BRAND_NAME}_Report_{scan['scan_id']}.pdf",
            mime="application/pdf",
            use_container_width=True
        )

    st.markdown("</div>", unsafe_allow_html=True)


# =========================
# Footer (discreet, not “demo/PoC”)
# =========================
st.markdown(
    """
<div class="footer-note">
  This platform provides <b>advisory risk signals</b> and <b>evidence outputs</b> to support community review and informed dialogue.
  It does not issue legal determinations or automated accusations.
</div>
""",
    unsafe_allow_html=True
)
