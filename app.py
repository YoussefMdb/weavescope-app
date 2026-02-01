import io
import os
import time
import random
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image, ImageDraw, ImageFilter

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


# =========================
# Branding
# =========================
BRAND_NAME = "WeaveScope"
TAGLINE = "AI-assisted detection of cultural design misuse in textiles"
ASSETS_DIR = "assets"  # put your logo here: assets/logo.png


# =========================
# Page setup
# =========================
st.set_page_config(
    page_title=BRAND_NAME,
    page_icon="🧵",
    layout="wide",
)


# =========================
# Helpers
# =========================
def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def stable_seed_from_bytes(b: bytes) -> int:
    if not b:
        return random.randint(0, 10**9)
    return int.from_bytes(b[:8], "little", signed=False)


def load_logo():
    path = os.path.join(ASSETS_DIR, "logo.png")
    if os.path.exists(path):
        try:
            return Image.open(path).convert("RGBA")
        except Exception:
            return None
    return None


def risk_level(score: float) -> str:
    if score >= 70:
        return "high"
    if score >= 35:
        return "med"
    return "low"


# =========================
# UI theme (palette inspired by your reference)
# =========================
st.markdown(
    """
<style>
:root{
  /* Inspired by parchment + silver metal + cobalt blue + antique gold */
  --bg0: #fbf7ef;
  --bg1: #f4efe3;
  --card: rgba(255,255,255,0.72);
  --card2: rgba(255,255,255,0.88);
  --stroke: rgba(15, 23, 42, 0.12);
  --stroke2: rgba(15, 23, 42, 0.18);
  --text: #0f172a;
  --muted: rgba(15,23,42,0.62);

  --blue: #1d4ed8;     /* cobalt */
  --blue2:#60a5fa;     /* light */
  --gold: #b08a2a;     /* antique gold */
  --silver:#9aa3ad;    /* metal */
  --ink:  #111827;

  --radius: 18px;
}

/* Layout */
.block-container {
  padding-top: 1rem;
  padding-bottom: 2.8rem;
  max-width: 1220px;
}

/* Hide Streamlit chrome */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Background */
.stApp {
  background:
    radial-gradient(900px 480px at 20% 10%, rgba(29,78,216,0.12), transparent 55%),
    radial-gradient(760px 420px at 86% 18%, rgba(176,138,42,0.14), transparent 55%),
    radial-gradient(980px 520px at 50% 92%, rgba(154,163,173,0.14), transparent 62%),
    linear-gradient(180deg, var(--bg0), var(--bg1));
}

/* Glass topbar */
.ws-topbar{
  display:flex; align-items:center; justify-content:space-between;
  padding: 14px 16px;
  border-radius: var(--radius);
  border: 1px solid var(--stroke);
  background: linear-gradient(180deg, rgba(255,255,255,0.70), rgba(255,255,255,0.45));
  backdrop-filter: blur(12px);
  box-shadow: 0 10px 26px rgba(15, 23, 42, 0.08);
}
.ws-brand{
  display:flex; gap:12px; align-items:center;
}
.ws-logo-slot{
  width: 46px; height: 46px;
  border-radius: 14px;
  border: 1px dashed rgba(29,78,216,0.35);
  background: linear-gradient(180deg, rgba(29,78,216,0.10), rgba(176,138,42,0.08));
  display:flex; align-items:center; justify-content:center;
  color: var(--muted);
  font-weight: 800;
}
.ws-title{
  font-weight: 900;
  letter-spacing: 0.2px;
  font-size: 16px;
  color: var(--text);
  line-height: 1.1;
}
.ws-sub{
  font-size: 12px;
  color: var(--muted);
  margin-top: 3px;
}
.ws-pills{
  display:flex; gap:10px; align-items:center;
}
.ws-pill{
  padding: 8px 10px;
  border-radius: 999px;
  border: 1px solid var(--stroke);
  background: rgba(255,255,255,0.55);
  font-size: 12px;
  color: var(--ink);
}
.ws-pill strong{ color: var(--blue); }

/* Hero */
.ws-hero{
  margin-top: 16px;
  border-radius: 22px;
  border: 1px solid var(--stroke);
  background:
    linear-gradient(135deg, rgba(255,255,255,0.62), rgba(255,255,255,0.36)),
    radial-gradient(520px 240px at 16% 20%, rgba(29,78,216,0.18), transparent 60%),
    radial-gradient(520px 240px at 82% 30%, rgba(176,138,42,0.18), transparent 60%);
  backdrop-filter: blur(12px);
  box-shadow: 0 20px 55px rgba(15,23,42,0.10);
  padding: 18px 18px 14px 18px;
}
.ws-hero h1{
  margin:0;
  font-size: 30px;
  letter-spacing: -0.4px;
  color: var(--text);
}
.ws-hero p{
  margin: 8px 0 0 0;
  color: rgba(15,23,42,0.74);
  font-size: 14px;
  line-height: 1.55;
}
.ws-kpis{
  margin-top: 14px;
  display:grid;
  grid-template-columns: repeat(4, 1fr);
  gap:10px;
}
.ws-kpi{
  padding: 12px;
  border-radius: 16px;
  border: 1px solid var(--stroke);
  background: rgba(255,255,255,0.62);
}
.ws-kpi .k{ font-size:12px; color: var(--muted); }
.ws-kpi .v{ font-size:18px; font-weight: 900; margin-top: 4px; color: var(--text); }
.ws-kpi .s{ font-size:12px; color: rgba(15,23,42,0.70); margin-top: 6px; }

/* Cards */
.ws-card{
  border-radius: 22px;
  border: 1px solid var(--stroke);
  background: rgba(255,255,255,0.68);
  backdrop-filter: blur(12px);
  box-shadow: 0 14px 34px rgba(15,23,42,0.08);
  padding: 14px;
}
.ws-card2{
  border-radius: 18px;
  border: 1px solid var(--stroke);
  background: rgba(255,255,255,0.78);
  padding: 12px;
}
.ws-card-title{
  font-size: 14px;
  font-weight: 900;
  color: var(--text);
  margin-bottom: 8px;
}
.ws-muted{ color: var(--muted); font-size: 12px; }
.ws-hr{ height: 1px; background: var(--stroke); margin: 10px 0; }

/* Badges */
.ws-badge{
  display:inline-flex; gap:8px; align-items:center;
  padding: 7px 10px;
  border-radius: 999px;
  border: 1px solid var(--stroke);
  font-weight: 900;
  font-size: 12px;
  background: rgba(255,255,255,0.65);
  color: var(--ink);
}
.ws-badge-high{ background: rgba(239,68,68,0.10); border-color: rgba(239,68,68,0.22); color:#7f1d1d; }
.ws-badge-med { background: rgba(245,158,11,0.12); border-color: rgba(245,158,11,0.25); color:#7c2d12; }
.ws-badge-low { background: rgba(34,197,94,0.10); border-color: rgba(34,197,94,0.22); color:#14532d; }

/* Tiles */
.ws-tile{
  border-radius: 18px;
  border: 1px solid var(--stroke);
  background: rgba(255,255,255,0.72);
  padding: 10px;
  box-shadow: 0 10px 26px rgba(15,23,42,0.06);
}
.ws-tile h4{
  margin: 8px 0 2px 0;
  font-size: 13px;
  color: var(--text);
  font-weight: 900;
}
.ws-tile p{
  margin: 0;
  font-size: 12px;
  color: rgba(15,23,42,0.72);
}

/* Buttons (Streamlit) */
.stButton>button {
  border-radius: 14px !important;
  border: 1px solid rgba(29,78,216,0.25) !important;
  background: linear-gradient(135deg, rgba(29,78,216,0.16), rgba(176,138,42,0.10)) !important;
  color: var(--text) !important;
  font-weight: 900 !important;
  padding: 0.65rem 0.9rem !important;
  box-shadow: 0 12px 24px rgba(15,23,42,0.10) !important;
}
.stButton>button:hover{
  border-color: rgba(29,78,216,0.42) !important;
  transform: translateY(-1px);
}

/* File uploader */
section[data-testid="stFileUploaderDropzone"]{
  border-radius: 18px !important;
  border: 1px dashed rgba(29,78,216,0.35) !important;
  background: rgba(255,255,255,0.52) !important;
}

/* Subtle animated glow ring */
@keyframes glow {
  0% { box-shadow: 0 0 0 rgba(29,78,216,0.0); }
  50% { box-shadow: 0 0 26px rgba(29,78,216,0.18); }
  100% { box-shadow: 0 0 0 rgba(29,78,216,0.0); }
}
.ws-glow{
  animation: glow 3.4s ease-in-out infinite;
}
</style>
""",
    unsafe_allow_html=True,
)


# =========================
# Textile swatches (keep: realistic cloth vibe)
# =========================
def textile_swatch(seed: int, size=(520, 520), style=None) -> Image.Image:
    rng = random.Random(seed)
    w, h = size
    style = style or rng.choice(["weave", "plaid", "herringbone", "stripes", "ikat_soft"])

    # Palette aligned with the theme
    base_sets = [
        [(17, 24, 39), (29, 78, 216), (251, 247, 239), (176, 138, 42)],
        [(17, 24, 39), (96, 165, 250), (244, 239, 227), (154, 163, 173)],
        [(17, 24, 39), (29, 78, 216), (244, 239, 227), (154, 163, 173)],
    ]
    c0, c1, c2, c3 = rng.choice(base_sets)

    img = Image.new("RGB", (w, h), c2)
    # subtle textile grain
    noise = np.random.default_rng(seed).integers(0, 20, size=(h, w, 1), dtype=np.uint8)
    noise_img = Image.fromarray(np.repeat(noise, 3, axis=2), "RGB")
    img = Image.blend(img, noise_img, 0.10)
    d = ImageDraw.Draw(img)

    if style == "weave":
        step = rng.choice([6, 8, 10])
        for x in range(0, w, step):
            col = c1 if (x // step) % 2 == 0 else c3
            d.line([(x, 0), (x, h)], fill=col, width=1)
        for y in range(0, h, step):
            col = c0 if (y // step) % 2 == 0 else c3
            d.line([(0, y), (w, y)], fill=col, width=1)
        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))

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
        for x in range(0, w, step // 2):
            d.line([(x, 0), (x, h)], fill=(255, 255, 255), width=1)
        img = img.filter(ImageFilter.GaussianBlur(radius=0.55))

    elif style == "herringbone":
        step = rng.choice([14, 16, 18])
        for y in range(0, h, step):
            for x in range(0, w, step):
                col = c1 if ((x // step + y // step) % 2 == 0) else c0
                d.polygon([(x, y), (x + step, y + step // 2), (x, y + step)], fill=col)
                d.polygon([(x + step, y), (x + step, y + step), (x, y + step // 2)], fill=c3)
        img = img.filter(ImageFilter.GaussianBlur(radius=0.65))

    elif style == "ikat_soft":
        band = rng.choice([40, 56, 72])
        for x in range(0, w, band):
            col = c1 if (x // band) % 2 == 0 else c0
            d.rectangle([x, 0, min(w, x + band), h], fill=col)
        img = img.filter(ImageFilter.GaussianBlur(radius=3.0))
        noise2 = np.random.default_rng(seed + 9).integers(0, 24, size=(h, w, 1), dtype=np.uint8)
        noise2_img = Image.fromarray(np.repeat(noise2, 3, axis=2), "RGB")
        img = Image.blend(img, noise2_img, 0.08)

    return img


def ai_highlight_overlay(img: Image.Image, seed: int) -> Image.Image:
    """Simulate AI attention/highlights (futuristic + clean)."""
    rng = random.Random(seed)
    base = img.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)

    w, h = base.size

    # soft "scan ring"
    ring = Image.new("RGBA", base.size, (0, 0, 0, 0))
    rd = ImageDraw.Draw(ring)
    cx, cy = w // 2, h // 2
    r = int(min(w, h) * 0.38)
    rd.ellipse([cx - r, cy - r, cx + r, cy + r], outline=(29, 78, 216, 160), width=10)
    ring = ring.filter(ImageFilter.GaussianBlur(1.6))
    overlay = Image.alpha_composite(overlay, ring)

    # highlight regions
    for _ in range(rng.randint(3, 5)):
        x0 = rng.randint(0, int(w * 0.55))
        y0 = rng.randint(0, int(h * 0.55))
        x1 = x0 + rng.randint(int(w * 0.22), int(w * 0.52))
        y1 = y0 + rng.randint(int(h * 0.22), int(h * 0.52))
        d.rounded_rectangle([x0, y0, x1, y1], radius=22, outline=(29, 78, 216, 220), width=6)
        d.rounded_rectangle([x0 + 6, y0 + 6, x1 - 6, y1 - 6], radius=18, fill=(29, 78, 216, 34))

    overlay = overlay.filter(ImageFilter.GaussianBlur(radius=1.1))
    return Image.alpha_composite(base, overlay).convert("RGB")


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
        f"Marketplaces: {meta.get('marketplaces','—')}",
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
            c.drawString(40, y - 48, f"Language signals: {', '.join(m['flags'])}")
        y -= 70

    c.setFont("Helvetica-Oblique", 8)
    c.drawString(40, 50, "Note: Advisory risk signal for community review. Not a legal determination.")
    c.save()
    buff.seek(0)
    return buff.read()


# =========================
# State
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
logo_img = load_logo()

left, right = st.columns([0.75, 0.25], gap="small")
with left:
    st.markdown('<div class="ws-topbar">', unsafe_allow_html=True)
    cA, cB = st.columns([0.12, 0.88], gap="small")
    with cA:
        if logo_img:
            st.image(logo_img, width=46)
        else:
            st.markdown('<div class="ws-logo-slot">LOGO</div>', unsafe_allow_html=True)
    with cB:
        st.markdown(
            f"""
            <div>
              <div class="ws-title">{BRAND_NAME}</div>
              <div class="ws-sub">{TAGLINE}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    st.markdown("</div>", unsafe_allow_html=True)

with right:
    st.markdown(
        f"""
        <div class="ws-topbar">
          <div class="ws-pills">
            <div class="ws-pill"><strong>AI</strong> monitoring</div>
            <div class="ws-pill">{now_str()}</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================
# Hero
# =========================
st.markdown(
    f"""
<div class="ws-hero ws-glow">
  <h1>Detect textile pattern misuse — with AI-guided evidence</h1>
  <p>
    Upload a textile pattern and surface similar items across marketplaces with ranked visual matches,
    context signals, and a transparent risk breakdown built for community review and professional reporting.
  </p>
  <div class="ws-kpis">
    <div class="ws-kpi"><div class="k">Visual match ranking</div><div class="v">Top-K</div><div class="s">Structure + motif overlap</div></div>
    <div class="ws-kpi"><div class="k">Context signals</div><div class="v">NLP</div><div class="s">Attribution & wording cues</div></div>
    <div class="ws-kpi"><div class="k">Explainable score</div><div class="v">0–100</div><div class="s">Drivers shown clearly</div></div>
    <div class="ws-kpi"><div class="k">Evidence export</div><div class="v">PDF</div><div class="s">Timestamp + source links</div></div>
  </div>
</div>
""",
    unsafe_allow_html=True,
)

st.write("")
tabs = st.tabs(["Search", "Monitoring", "Registry", "Reports"])


# =========================
# Tab: Search
# =========================
with tabs[0]:
    left, right = st.columns([0.58, 0.42], gap="large")

    with left:
        st.markdown('<div class="ws-card"><div class="ws-card-title">Submit a textile pattern</div>', unsafe_allow_html=True)

        uploaded = st.file_uploader(
            "Pattern image (fabric, embroidery, print, weave)",
            type=["png", "jpg", "jpeg"],
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
                default=["CatalogX", "DemoMarket"],
            )
        with c4:
            top_k = st.slider("Results", 3, 12, 6)

        st.markdown('<div class="ws-hr"></div>', unsafe_allow_html=True)

        c5, c6 = st.columns([0.62, 0.38], gap="small")
        with c5:
            run = st.button("✨ Analyze with AI", use_container_width=True)
        with c6:
            sample = st.button("Use a sample textile swatch", use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="ws-card"><div class="ws-card-title">Preview</div>', unsafe_allow_html=True)

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
            seed = 424242
            query_img = textile_swatch(seed, style="weave")

        st.image(query_img, use_container_width=True)
        st.markdown('<div class="ws-muted">Tip: close-up fabric photos produce the strongest matches.</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if run:
        meta = {
            "culture": culture or "—",
            "origin": origin or "—",
            "meaning": (meaning[:180] + "…") if len(meaning) > 180 else (meaning or "—"),
            "sensitivity": sensitivity,
            "consent": consent,
            "marketplaces": ", ".join(marketplaces) if marketplaces else "—",
            "created_at": now_str(),
        }

        # Simulated pipeline (credible + marketing)
        with st.status("AI pipeline running", expanded=True) as status:
            st.write("Preprocessing image • normalization • denoise")
            time.sleep(0.20)
            st.write("Extracting multi-scale pattern signature")
            time.sleep(0.20)
            st.write("Embedding search • scanning marketplace index")
            time.sleep(0.20)
            st.write("Context reading • attribution & wording cues")
            time.sleep(0.20)
            st.write("Generating explainable score + evidence pack")
            time.sleep(0.20)
            status.update(label="Analysis complete", state="complete", expanded=False)

        highlighted = ai_highlight_overlay(query_img, seed)

        titles = [
            "Woven Jacquard Jacket", "Printed Scarf (Limited Run)", "Decor Textile Cushion",
            "Embroidery Panel Bag", "Patterned Wrap Dress", "Home Textile Wall Hanging",
            "Cotton Kimono Robe", "Handmade Tote with Motif",
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

            sw = textile_swatch(seed + i * 91 + 7, style=rng.choice(["weave", "plaid", "herringbone", "stripes", "ikat_soft"]))
            attribution = "present" if rng.random() < 0.35 else "absent"
            flags = pick_flags(rng)
            url = f"https://{rng.choice(sources).lower()}.example.com/listing/{seed % 9999}-{i}"

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
                "url": url,
            })

        rows = sorted(rows, key=lambda r: (r["score"], r["similarity"]), reverse=True)

        st.session_state.scan = {
            "meta": meta,
            "query_img": query_img,
            "highlighted": highlighted,
            "rows": rows,
            "scan_id": f"WS-{random.randint(10000, 99999)}",
        }

        st.session_state.registry.insert(0, {
            "id": f"ITEM-{len(st.session_state.registry) + 1:03d}",
            "culture": meta["culture"],
            "origin": meta["origin"],
            "sensitivity": meta["sensitivity"],
            "consent": meta["consent"],
            "created_at": meta["created_at"],
        })

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
                        "url": r["url"],
                    })

        st.success("Results ready. Review insights and evidence below.")

        st.write("")
        st.markdown('<div class="ws-card"><div class="ws-card-title">AI insights</div>', unsafe_allow_html=True)

        cA, cB = st.columns([1, 1], gap="large")
        with cA:
            st.markdown('<div class="ws-muted">Attention map & salient regions</div>', unsafe_allow_html=True)
            st.image(highlighted, use_container_width=True)

        with cB:
            top = rows[0]
            badge_class = "ws-badge-high" if top["level"] == "high" else "ws-badge-med" if top["level"] == "med" else "ws-badge-low"
            badge_label = "High risk" if top["level"] == "high" else "Medium risk" if top["level"] == "med" else "Low risk"

            st.markdown(
                f'<div class="ws-badge {badge_class}">● {badge_label} — {top["score"]}/100</div>',
                unsafe_allow_html=True,
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
        st.markdown('<div class="ws-card"><div class="ws-card-title">Top matches across marketplaces</div>', unsafe_allow_html=True)

        cols = st.columns(3, gap="large")
        for i, r in enumerate(rows[:6]):
            with cols[i % 3]:
                st.markdown('<div class="ws-tile">', unsafe_allow_html=True)
                st.image(r["img"], use_container_width=True)
                st.markdown(f"<h4>{r['title']}</h4>", unsafe_allow_html=True)
                st.markdown(f"<p>{r['brand']} • {r['source']}</p>", unsafe_allow_html=True)

                badge_class = "ws-badge-high" if r["level"] == "high" else "ws-badge-med" if r["level"] == "med" else "ws-badge-low"
                badge_label = "High" if r["level"] == "high" else "Medium" if r["level"] == "med" else "Low"
                st.markdown(
                    f'<div class="ws-badge {badge_class}">Risk {badge_label} • {r["score"]}/100</div>',
                    unsafe_allow_html=True,
                )

                st.caption(r["url"])
                st.progress(r["similarity"])
                st.markdown(
                    f"<div class='ws-muted'>Similarity: <b>{r['similarity']}%</b> • Attribution: <b>{r['attribution']}</b></div>",
                    unsafe_allow_html=True,
                )
                if r["flags"]:
                    st.markdown(
                        f"<div class='ws-muted'>Language signals: <b>{', '.join(r['flags'])}</b></div>",
                        unsafe_allow_html=True,
                    )

                st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        st.write("")
        pdf = make_pdf_report(BRAND_NAME, query_img, meta, rows)
        st.download_button(
            "Download evidence report (PDF)",
            data=pdf,
            file_name=f"{BRAND_NAME}_Report_{st.session_state.scan['scan_id']}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )


# =========================
# Tab: Monitoring
# =========================
with tabs[1]:
    st.markdown('<div class="ws-card"><div class="ws-card-title">Monitoring & alerts</div>', unsafe_allow_html=True)
    st.markdown("<div class='ws-muted'>High-risk listings are surfaced when similarity and context signals exceed the threshold.</div>", unsafe_allow_html=True)
    st.markdown('<div class="ws-hr"></div>', unsafe_allow_html=True)

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
                    index=["New", "In review", "Ignored", "Flagged"].index(a["status"]) if a["status"] in ["New", "In review", "Ignored", "Flagged"] else 0,
                    key=f"st_{idx}",
                )
                st.session_state.alerts[idx]["status"] = new_status

    st.markdown("</div>", unsafe_allow_html=True)


# =========================
# Tab: Registry
# =========================
with tabs[2]:
    st.markdown('<div class="ws-card"><div class="ws-card-title">Cultural registry</div>', unsafe_allow_html=True)
    st.markdown("<div class='ws-muted'>Submitted items and consent settings.</div>", unsafe_allow_html=True)
    st.markdown('<div class="ws-hr"></div>', unsafe_allow_html=True)

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
    st.markdown('<div class="ws-card"><div class="ws-card-title">Reports</div>', unsafe_allow_html=True)
    st.markdown("<div class='ws-muted'>Generate and share evidence packages with timestamps and source links.</div>", unsafe_allow_html=True)
    st.markdown('<div class="ws-hr"></div>', unsafe_allow_html=True)

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
            use_container_width=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)


# =========================
# Footer (discreet)
# =========================
st.markdown(
    """
<div class="ws-card2" style="margin-top:16px;">
  <div class="ws-muted">
    WeaveScope provides advisory risk signals and evidence outputs to support community review and informed dialogue.
    It does not issue legal determinations or automated accusations.
  </div>
</div>
""",
    unsafe_allow_html=True,
)
