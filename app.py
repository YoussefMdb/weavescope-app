import io
import os
import time
import random
from datetime import datetime

import numpy as np
import pandas as pd
import streamlit as st
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader


# =========================
# Brand
# =========================
BRAND_NAME = "WeaveScope"
TAGLINE = "AI-guided detection of cultural design misuse in textiles"
ASSETS_DIR = "assets"  # put assets/logo.png here


st.set_page_config(page_title=BRAND_NAME, page_icon="🧵", layout="wide")


# =========================
# Helpers
# =========================
def img(image, *, caption=None, full=True, width=None):
    """Compatibility between old/new Streamlit image APIs."""
    if width is not None:
        return st.image(image, caption=caption, width=width)
    if full:
        try:
            return st.image(image, caption=caption, use_container_width=True)
        except TypeError:
            return st.image(image, caption=caption, use_column_width=True)
    return st.image(image, caption=caption)


def now_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def clamp(x, a=0.0, b=100.0):
    return max(a, min(b, x))


def stable_seed_from_bytes(b: bytes) -> int:
    if not b:
        return random.randint(0, 10**9)
    return int.from_bytes(b[:8], "little", signed=False)


def risk_level(score: float) -> str:
    if score >= 70:
        return "high"
    if score >= 35:
        return "med"
    return "low"


def badge_html(level: str, text: str, score: float = None):
    cls = "b-high" if level == "high" else "b-med" if level == "med" else "b-low"
    if score is None:
        return f'<span class="badge {cls}">● {text}</span>'
    return f'<span class="badge {cls}">● {text}<span class="badgeScore">{score:.1f}</span></span>'


def load_logo():
    p = os.path.join(ASSETS_DIR, "logo.png")
    if os.path.exists(p):
        try:
            return Image.open(p).convert("RGBA")
        except Exception:
            return None
    return None


# =========================
# CSS (NO empty rectangles)
# =========================
st.markdown(
    """
<style>
:root{
  --bg0:#070b16;
  --bg1:#081433;

  --text:#F1F5FF;
  --muted: rgba(241,245,255,0.72);

  /* textile palette */
  --blue:#5DA9FF;
  --gold:#C9A03A;
  --teal:#2DD4BF;
  --mag:#E879F9;
  --copper:#F97316;
  --crimson:#EF4444;
  --silver:#A9B2BD;

  --stroke: rgba(255,255,255,0.12);
  --stroke2: rgba(255,255,255,0.18);
}

.block-container{max-width: 1320px; padding-top: 1.1rem; padding-bottom: 2.4rem;}
#MainMenu, footer, header{visibility:hidden;}

.stApp{
  background:
    radial-gradient(900px 520px at 16% 12%, rgba(93,169,255,0.22), transparent 60%),
    radial-gradient(820px 520px at 86% 16%, rgba(233,121,249,0.16), transparent 60%),
    radial-gradient(980px 640px at 50% 92%, rgba(45,212,191,0.12), transparent 62%),
    radial-gradient(780px 520px at 62% 32%, rgba(239,68,68,0.12), transparent 60%),
    radial-gradient(780px 520px at 70% 70%, rgba(201,160,58,0.12), transparent 60%),
    radial-gradient(900px 520px at 28% 62%, rgba(249,115,22,0.10), transparent 58%),
    linear-gradient(180deg, var(--bg0), var(--bg1));
}

.hero{
  width: 100%;
  text-align: center !important;
}

.heroName, .heroTag{
  width: 100%;
  text-align: center !important;
  margin-left: auto !important;
  margin-right: auto !important;
}

/* Sidebar */
section[data-testid="stSidebar"]{
  background: rgba(255,255,255,0.04) !important;
  border-right: 1px solid var(--stroke);
}
section[data-testid="stSidebar"] *{color: var(--text) !important;}
div[data-testid="stSidebarNav"]{display:none;}

/* ===== Centered header (no frames / no empty blocks) ===== */
.hero{
  text-align:center;
  margin: 8px 0 16px 0;
}

/* Hide Streamlit image fullscreen button (circle with arrows) */
button[title="View fullscreen"] { display: none !important; }
button[title="View full screen"] { display: none !important; }
button[title="Fullscreen"] { display: none !important; }

.heroLogo{
  width: 0px;
  margin: 0px auto 0px auto;
  filter: drop-shadow(0 24px 60px rgba(0,0,0,0.55));
}
.heroName{
  font-size: 26px;
  font-weight: 950;
  letter-spacing: 0.2px;
  color: var(--text);
}
.heroTag{
  font-size: 12.5px;
  color: rgba(241,245,255,0.76);
  margin-top: 4px;
}
.heroTitle{
  margin: 14px auto 0 auto;
  font-size: 44px;
  line-height: 1.05;
  letter-spacing: -0.9px;
  font-weight: 950;
  color: var(--text);
  max-width: 980px;
}
.heroText{
  margin: 10px auto 0 auto;
  color: rgba(241,245,255,0.84);
  font-size: 14px;
  line-height: 1.75;
  max-width: 940px;
}

/* Pills */
.pillRow{
  margin-top: 14px;
  display:flex; flex-wrap:wrap; gap:10px;
  justify-content:center;
}
.pill{
  padding: 8px 12px; border-radius: 999px;
  border: 1px solid var(--stroke);
  background: rgba(255,255,255,0.04);
  color: rgba(241,245,255,0.78);
  font-size: 12px;
  font-weight: 900;
}
.pill b{color: var(--text);}
.dot{display:inline-block; width:8px; height:8px; border-radius:999px; margin-right:8px;}
.dot-blue{background: var(--blue);}
.dot-gold{background: var(--gold);}
.dot-teal{background: var(--teal);}
.dot-mag{background: var(--mag);}
.dot-red{background: var(--crimson);}
.dot-copper{background: var(--copper);}

/* CTA row */
.ctaRow{
  margin-top: 14px;
  display:flex;
  gap:10px;
  justify-content:center;
  flex-wrap:wrap;
}
.ctaGhost{
  display:inline-flex; align-items:center; gap:10px;
  padding: 10px 12px; border-radius: 14px;
  border: 1px solid rgba(255,255,255,0.14);
  background: rgba(255,255,255,0.04);
  color: rgba(241,245,255,0.78);
  font-size: 12px; font-weight: 900;
}

/* Cards */
.card{
  border-radius: 22px;
  border: 1px solid var(--stroke);
  background: rgba(255,255,255,0.05);
  backdrop-filter: blur(14px);
  box-shadow: 0 18px 58px rgba(0,0,0,0.34);
  padding: 14px;
}
.title{font-size: 14px; font-weight: 950; color: var(--text); margin-bottom: 8px;}
.muted{color: var(--muted); font-size: 12px;}
.hr{height:1px; background: var(--stroke); margin: 12px 0;}

/* Badges */
.badge{
  display:inline-flex; align-items:center; gap:8px;
  padding: 7px 10px; border-radius: 999px;
  border: 1px solid var(--stroke);
  font-weight: 950; font-size: 12px; color: var(--text);
  background: rgba(255,255,255,0.04);
}
.badgeScore{
  margin-left: 2px; padding: 2px 8px; border-radius: 999px;
  border: 1px solid var(--stroke2); background: rgba(0,0,0,0.22);
}
.b-high{border-color: rgba(239,68,68,0.35); background: rgba(239,68,68,0.10);}
.b-med {border-color: rgba(245,158,11,0.35); background: rgba(245,158,11,0.10);}
.b-low {border-color: rgba(34,197,94,0.35); background: rgba(34,197,94,0.10);}

/* Buttons */
.stButton>button{
  border-radius: 14px !important;
  border: 1px solid rgba(255,255,255,0.14) !important;
  background:
    linear-gradient(135deg,
      rgba(93,169,255,0.22),
      rgba(233,121,249,0.16),
      rgba(45,212,191,0.12),
      rgba(201,160,58,0.10),
      rgba(239,68,68,0.10),
      rgba(249,115,22,0.10)
    ) !important;
  color: var(--text) !important;
  font-weight: 950 !important;
  box-shadow: 0 18px 46px rgba(0,0,0,0.40) !important;
}
.stButton>button:hover{
  transform: translateY(-1px);
  border-color: rgba(255,255,255,0.22) !important;
}

/* Uploader */
section[data-testid="stFileUploaderDropzone"]{
  border-radius: 18px !important;
  border: 1px dashed rgba(255,255,255,0.18) !important;
  background: rgba(255,255,255,0.03) !important;
}

div[data-testid="stToolbar"]{display:none;}
</style>
""",
    unsafe_allow_html=True,
)


# =========================
# Textile visuals
# =========================
def textile_swatch(seed: int, size=(560, 560), style=None) -> Image.Image:
    rng = random.Random(seed)
    w, h = size
    style = style or rng.choice(["weave", "stripes", "plaid", "ikat", "chevron"])

    palette = [
        (10, 18, 48),
        (93, 169, 255),
        (201, 160, 58),
        (45, 212, 191),
        (233, 121, 249),
        (249, 115, 22),
        (239, 68, 68),
        (169, 178, 189),
    ]
    c0, c1, c3, c4, c5, c6, cR, c7 = palette

    img0 = Image.new("RGB", (w, h), (10, 18, 48))

    noise = np.random.default_rng(seed).integers(0, 26, size=(h, w, 1), dtype=np.uint8)
    noise_img = Image.fromarray(np.repeat(noise, 3, axis=2), "RGB")
    img0 = Image.blend(img0, noise_img, 0.12)
    d = ImageDraw.Draw(img0)

    if style == "weave":
        step = rng.choice([7, 9, 11])
        colsA = [c1, c5, c6, cR]
        colsB = [c0, c3, c4, c7]
        for x in range(0, w, step):
            d.line([(x, 0), (x, h)], fill=colsA[(x // step) % len(colsA)], width=1)
        for y in range(0, h, step):
            d.line([(0, y), (w, y)], fill=colsB[(y // step) % len(colsB)], width=1)

    elif style == "stripes":
        stripe = rng.choice([18, 26, 34])
        cols = [c1, c6, cR, c3, c5, c4, c7]
        for i, x in enumerate(range(0, w, stripe)):
            d.rectangle([x, 0, min(w, x + stripe - 2), h], fill=cols[i % len(cols)])

    elif style == "plaid":
        step = rng.choice([24, 30, 36])
        for x in range(0, w, step):
            d.rectangle([x, 0, min(w, x + 6), h], fill=c1)
        for y in range(0, h, step):
            d.rectangle([0, y, w, min(h, y + 6)], fill=c6)
        thin = max(2, step // 12)
        for x in range(0, w, step // 2):
            d.rectangle([x, 0, min(w, x + thin), h], fill=cR)

    elif style == "ikat":
        band = rng.choice([42, 60, 78])
        cols = [c1, c6, cR, c7, c3, c4, c5]
        for x in range(0, w, band):
            d.rectangle([x, 0, min(w, x + band), h], fill=cols[(x // band) % len(cols)])
        img0 = img0.filter(ImageFilter.GaussianBlur(3.2))
        img0 = ImageEnhance.Contrast(img0).enhance(1.08)

    else:  # chevron
        step = rng.choice([16, 20, 24])
        cols = [c1, c6, cR, c3, c4, c5, c7]
        for y in range(0, h, step):
            for x in range(0, w, step):
                col = cols[(x // step + y // step) % len(cols)]
                midx = x + step // 2
                d.line([(x, y), (midx, y + step)], fill=col, width=2)
                d.line([(midx, y + step), (x + step, y)], fill=col, width=2)

    img0 = img0.filter(ImageFilter.GaussianBlur(0.55))
    return img0


def ai_highlight_overlay(img0: Image.Image, seed: int) -> Image.Image:
    rng = random.Random(seed)
    base = img0.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(overlay)
    w, h = base.size

    y = rng.randint(int(h * 0.25), int(h * 0.75))
    d.rectangle([0, y - 6, w, y + 6], fill=(93, 169, 255, 40))
    overlay = overlay.filter(ImageFilter.GaussianBlur(1.6))

    d = ImageDraw.Draw(overlay)
    for _ in range(rng.randint(3, 5)):
        x0 = rng.randint(0, int(w * 0.55))
        y0 = rng.randint(0, int(h * 0.55))
        x1 = x0 + rng.randint(int(w * 0.22), int(w * 0.52))
        y1 = y0 + rng.randint(int(h * 0.22), int(h * 0.52))
        d.rounded_rectangle([x0, y0, x1, y1], radius=22, outline=(233, 121, 249, 220), width=5)
        d.rounded_rectangle([x0 + 6, y0 + 6, x1 - 6, y1 - 6], radius=18, fill=(45, 212, 191, 22))

    overlay = overlay.filter(ImageFilter.GaussianBlur(1.0))
    return Image.alpha_composite(base, overlay).convert("RGB")


def make_pdf_report(brand: str, query_img: Image.Image, meta: dict, matches: list) -> bytes:
    buff = io.BytesIO()
    c = canvas.Canvas(buff, pagesize=A4)
    W, H = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, H - 42, f"{brand} — Evidence Report")
    c.setFont("Helvetica", 9)
    c.drawString(40, H - 58, f"Generated: {now_str()} • Scan ID: {meta.get('scan_id','—')}")

    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, H - 90, "Submitted textile pattern")
    img_buf = io.BytesIO()
    query_img.resize((220, 220)).save(img_buf, format="PNG")
    img_buf.seek(0)
    c.drawImage(ImageReader(img_buf), 40, H - 330, width=220, height=220, mask="auto")

    c.setFont("Helvetica", 9)
    x = 280
    y = H - 105
    lines = [
        f"Culture / Community: {meta.get('culture','—')}",
        f"Geographic origin: {meta.get('origin','—')}",
        f"Sensitivity: {meta.get('sensitivity','—')}",
        f"Consent: {meta.get('consent','—')}",
        f"Marketplaces: {meta.get('marketplaces','—')}",
        f"Timestamp: {meta.get('created_at','—')}",
    ]
    for i, ln in enumerate(lines):
        c.drawString(x, y - 16 * i, ln)

    c.setFont("Helvetica-Bold", 11)
    c.drawString(40, H - 370, "Top matches (evidence)")
    y = H - 390
    c.setFont("Helvetica", 9)

    for idx, m in enumerate(matches[:4], start=1):
        if y < 120:
            c.showPage()
            y = H - 60
        c.setFont("Helvetica-Bold", 9)
        c.drawString(40, y, f"{idx}. {m['title']} — Risk {m['score']}/100")
        c.setFont("Helvetica", 8)
        c.drawString(40, y - 12, f"Brand: {m['brand']} | Source: {m['source']}")
        c.drawString(40, y - 24, f"URL: {m['url']}")
        c.drawString(40, y - 36, f"Visual similarity: {m['similarity']}% | Attribution: {m['attribution']}")
        if m["flags"]:
            c.drawString(40, y - 48, f"Language signals: {', '.join(m['flags'])}")
        y -= 70

    c.setFont("Helvetica-Oblique", 8)
    c.drawString(40, 50, "Advisory risk signal for community review. Not a legal determination.")
    c.save()
    buff.seek(0)
    return buff.read()


def ensure_state():
    if "registry" not in st.session_state:
        st.session_state.registry = []
    if "alerts" not in st.session_state:
        st.session_state.alerts = []
    if "scan" not in st.session_state:
        st.session_state.scan = None
    if "scan_history" not in st.session_state:
        st.session_state.scan_history = []

    if not st.session_state.registry:
        st.session_state.registry = [
            {"id":"ITEM-001","culture":"Tunisian textile heritage","origin":"Tunisia","sensitivity":"Ceremonial","consent":"Community shared","created_at":now_str()},
            {"id":"ITEM-002","culture":"Regional weaving motif","origin":"North Africa","sensitivity":"Everyday","consent":"Monitoring enabled","created_at":now_str()},
        ]
    if not st.session_state.alerts:
        st.session_state.alerts = [
            {"created_at":now_str(),"title":"Patterned Wrap Dress","brand":"Studio Loom","risk":78.4,"similarity":88,"status":"New","url":"https://demomarket.example.com/listing/3081-2"},
            {"created_at":now_str(),"title":"Decor Textile Cushion","brand":"Urban Nomad","risk":62.9,"similarity":81,"status":"In review","url":"https://catalogx.example.com/listing/7721-1"},
        ]


ensure_state()


# =========================
# Sidebar
# =========================
st.sidebar.markdown(f"### {BRAND_NAME}")
page = st.sidebar.radio("Navigation", ["Search", "Monitoring", "Registry", "Reports"], index=0)
st.sidebar.markdown("---")
showcase = st.sidebar.toggle("Showcase mode", value=True)
st.sidebar.caption("Keeps UI full without real backend.")


# =========================
# Header (centered logo, NO rectangles)
# =========================
def crop_transparent(im: Image.Image, padding: int = 10) -> Image.Image:
    """Crop transparent borders so the symbol fills the canvas."""
    im = im.convert("RGBA")
    bbox = im.getbbox()
    if not bbox:
        return im
    x0, y0, x1, y1 = bbox
    x0 = max(0, x0 - padding)
    y0 = max(0, y0 - padding)
    x1 = min(im.width, x1 + padding)
    y1 = min(im.height, y1 + padding)
    return im.crop((x0, y0, x1, y1))

@st.cache_data(show_spinner=False)
def load_logo_cropped() -> Image.Image | None:
    p = os.path.join(ASSETS_DIR, "logo.png")
    if not os.path.exists(p):
        return None
    try:
        im = Image.open(p).convert("RGBA")
        im = crop_transparent(im, padding=8)
        return im
    except Exception:
        return None


logo = load_logo_cropped()



st.markdown('<div class="hero">', unsafe_allow_html=True)

if logo:
    # Center the image using columns
    c1, c2, c3 = st.columns([1, 1, 1])
    with c2:
        st.markdown('<div class="heroLogo">', unsafe_allow_html=True)
        img(logo, full=False, width=400)
        st.markdown("</div>", unsafe_allow_html=True)
else:
    st.markdown('<div class="heroLogo">🧵</div>', unsafe_allow_html=True)
st.markdown('<div class="hero">', unsafe_allow_html=True)

st.markdown(f'<div class="heroName">{BRAND_NAME}</div>', unsafe_allow_html=True)
st.markdown(f'<div class="heroTag">{TAGLINE}</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)



st.markdown(
    """
    <div class="heroTitle">Detect textile pattern misuse with explainable AI evidence</div>
    <div class="heroText">
      Upload a cultural textile motif, scan marketplaces, and receive transparent similarity + context signals.
      Designed for community review — with exportable evidence packs for dialogue, advocacy, and escalation when needed.
    </div>
    """,
    unsafe_allow_html=True,
)

ctaA, ctaB, ctaC = st.columns([1, 1, 1])
with ctaB:
    go_scan = st.button("✨ Start a scan", use_container_width=True)

st.markdown(
    """
    <div class="ctaRow">
      <div class="ctaGhost">🧠 Similarity + narrative cues</div>
      <div class="ctaGhost">📄 Evidence PDF • URLs + timestamps</div>
      <div class="ctaGhost">🫱 Human review • no auto-accusation</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="pillRow">
      <div class="pill"><span class="dot dot-blue"></span><b>Visual match</b> • motif similarity</div>
      <div class="pill"><span class="dot dot-mag"></span><b>Explainable</b> • drivers shown</div>
      <div class="pill"><span class="dot dot-teal"></span><b>Context cues</b> • attribution language</div>
      <div class="pill"><span class="dot dot-gold"></span><b>Export</b> • evidence pack</div>
      <div class="pill"><span class="dot dot-red"></span><b>Community-first</b> • consent & control</div>
      <div class="pill"><span class="dot dot-copper"></span><b>Textile-native</b> • woven motif focus</div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown("</div>", unsafe_allow_html=True)
st.write("")

if go_scan:
    st.sidebar.success("Go to Search → upload a pattern and run the scan.")


# =========================
# Simulated scan
# =========================
def run_simulated_scan(query_img: Image.Image, seed: int, sensitivity: str, marketplaces: list, top_k: int):
    rng = random.Random(seed)
    scan_id = f"WS-{random.randint(10000, 99999)}"

    titles = [
        "Woven Jacquard Jacket",
        "Printed Scarf (Limited Run)",
        "Decor Textile Cushion",
        "Embroidery Panel Bag",
        "Patterned Wrap Dress",
        "Home Textile Wall Hanging",
        "Cotton Robe",
        "Handmade Tote with Motif",
    ]
    brands = ["Maison Lume", "Studio Loom", "North & Co", "Atelier Vale", "Kora Works", "Urban Nomad"]
    sources = marketplaces if marketplaces else ["CatalogX", "DemoMarket", "CraftHub"]

    def pick_flags():
        pool = ["tribal", "exotic", "ethnic", "primitive", "oriental-inspired"]
        return [rng.choice(pool)] if rng.random() < 0.40 else []

    rows = []
    for i in range(top_k):
        sim = rng.uniform(62, 92)
        score = (
            0.52 * sim
            + (30 if sensitivity == "Sacred" else 18 if sensitivity == "Ceremonial" else 7)
            + (10 if rng.random() < 0.6 else 4)
        )
        score = clamp(score, 0, 100)
        lvl = risk_level(score)

        sw = textile_swatch(seed + i * 91 + 7, style=rng.choice(["weave", "plaid", "stripes", "ikat", "chevron"]))
        attribution = "present" if rng.random() < 0.32 else "absent"
        flags = pick_flags()
        src = rng.choice(sources)
        url = f"https://{src.lower()}.example.com/listing/{seed % 9999}-{i}"

        rows.append(
            {
                "rank": i + 1,
                "title": rng.choice(titles),
                "brand": rng.choice(brands),
                "source": src,
                "similarity": int(sim),
                "score": round(score, 1),
                "level": lvl,
                "attribution": attribution,
                "flags": flags,
                "img": sw,
                "url": url,
            }
        )

    rows = sorted(rows, key=lambda r: (r["score"], r["similarity"]), reverse=True)
    return scan_id, rows


# =========================
# Pages
# =========================
if page == "Search":
    left, right = st.columns([0.56, 0.44], gap="large")

    with left:
        st.markdown('<div class="card"><div class="title">Submit a textile pattern</div>', unsafe_allow_html=True)

        uploaded = st.file_uploader("Upload textile pattern image", type=["png", "jpg", "jpeg"])

        c1, c2 = st.columns(2)
        with c1:
            culture = st.text_input("Culture / community", placeholder="e.g., Tunisian textile heritage")
            origin = st.text_input("Geographic origin", placeholder="e.g., Tunisia")
        with c2:
            sensitivity = st.selectbox("Sensitivity", ["Everyday", "Ceremonial", "Sacred"], index=1)
            consent = st.selectbox("Consent", ["Private", "Community shared", "Monitoring enabled"], index=2)

        meaning = st.text_area("Meaning / function (optional)", placeholder="Short cultural context…", height=90)

        c3, c4 = st.columns(2)
        with c3:
            marketplaces = st.multiselect("Marketplaces", ["CatalogX", "DemoMarket", "CraftHub"], default=["CatalogX", "DemoMarket"])
        with c4:
            top_k = st.slider("Top matches", 3, 12, 6)

        st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
        run = st.button("✨ Run AI analysis", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="card"><div class="title">Preview</div>', unsafe_allow_html=True)

        if uploaded:
            img_bytes = uploaded.getvalue()
            query_img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
            seed = stable_seed_from_bytes(img_bytes)
        else:
            seed = 424242
            query_img = textile_swatch(seed, style=random.choice(["plaid", "ikat", "chevron"])) if showcase else textile_swatch(seed, style="weave")

        img(query_img, full=True)
        st.markdown('<div class="muted">Tip: close-up fabric photos produce the strongest evidence.</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    if run:
        meta = {
            "culture": culture or "—",
            "origin": origin or "—",
            "meaning": (meaning[:220] + "…") if len(meaning) > 220 else (meaning or "—"),
            "sensitivity": sensitivity,
            "consent": consent,
            "marketplaces": ", ".join(marketplaces) if marketplaces else "—",
            "created_at": now_str(),
        }

        with st.status("AI analysis running", expanded=True) as status:
            st.write("Image preprocessing • normalization • denoise")
            time.sleep(0.15)
            st.write("Pattern signature • multi-scale feature extraction")
            time.sleep(0.15)
            st.write("Similarity search • scanning marketplace index")
            time.sleep(0.15)
            st.write("Context reading • attribution & language cues")
            time.sleep(0.15)
            st.write("Risk model • explainable scoring & evidence pack")
            time.sleep(0.15)
            status.update(label="Analysis complete", state="complete", expanded=False)

        scan_id, rows = run_simulated_scan(query_img, seed, sensitivity, marketplaces, top_k)
        meta["scan_id"] = scan_id

        st.session_state.scan = {"meta": meta, "query_img": query_img, "rows": rows, "scan_id": scan_id}
        st.session_state.scan_history.insert(0, {
            "scan_id": scan_id,
            "created_at": meta["created_at"],
            "marketplaces": meta["marketplaces"],
            "top_risk": rows[0]["score"],
            "top_similarity": rows[0]["similarity"],
        })

        st.success("Insights and evidence are ready.")

        st.write("")
        st.markdown('<div class="card"><div class="title">Top matches</div>', unsafe_allow_html=True)
        cols = st.columns(3, gap="large")
        for i, r in enumerate(rows[:6]):
            with cols[i % 3]:
                st.markdown('<div class="card">', unsafe_allow_html=True)
                img(r["img"], full=True)
                st.markdown(f"**{r['title']}**")
                st.caption(f"{r['brand']} • {r['source']}")
                lab = "High" if r["level"] == "high" else "Medium" if r["level"] == "med" else "Low"
                st.markdown(badge_html(r["level"], f"Risk {lab}", r["score"]), unsafe_allow_html=True)
                st.caption(r["url"])
                st.progress(r["similarity"])
                st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

        st.write("")
        pdf = make_pdf_report(BRAND_NAME, query_img, meta, rows)
        st.download_button(
            "Download evidence report (PDF)",
            data=pdf,
            file_name=f"{BRAND_NAME}_Report_{scan_id}.pdf",
            mime="application/pdf",
            use_container_width=True,
        )

elif page == "Monitoring":
    st.markdown('<div class="card"><div class="title">Monitoring & alerts</div>', unsafe_allow_html=True)
    st.markdown("<div class='muted'>High-risk matches are surfaced for community review. No automatic accusations.</div>", unsafe_allow_html=True)
    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

    for idx, a in enumerate(st.session_state.alerts[:10]):
        c1, c2, c3, c4 = st.columns([2.2, 0.8, 0.9, 1.1], gap="small")
        with c1:
            st.markdown(f"**{a['title']}**  \n{a['brand']}")
            st.caption(a["url"])
            st.caption(f"Detected: {a['created_at']}")
        with c2:
            st.metric("Risk", f"{a['risk']}/100")
        with c3:
            st.metric("Similarity", f"{a['similarity']}%")
        with c4:
            new_status = st.selectbox(
                "Status",
                ["New", "In review", "Ignored", "Flagged"],
                index=["New", "In review", "Ignored", "Flagged"].index(a["status"]) if a["status"] in ["New", "In review", "Ignored", "Flagged"] else 0,
                key=f"al_{idx}",
            )
            st.session_state.alerts[idx]["status"] = new_status

    st.markdown("</div>", unsafe_allow_html=True)

elif page == "Registry":
    st.markdown('<div class="card"><div class="title">Cultural registry</div>', unsafe_allow_html=True)
    st.markdown("<div class='muted'>Submitted cultural items + consent settings.</div>", unsafe_allow_html=True)
    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)
    st.dataframe(pd.DataFrame(st.session_state.registry), use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

elif page == "Reports":
    st.markdown('<div class="card"><div class="title">Reports</div>', unsafe_allow_html=True)
    st.markdown("<div class='muted'>Evidence packages with timestamps and source links.</div>", unsafe_allow_html=True)
    st.markdown('<div class="hr"></div>', unsafe_allow_html=True)

    if st.session_state.scan_history:
        st.markdown("**Recent scans**")
        st.dataframe(pd.DataFrame(st.session_state.scan_history[:12]), use_container_width=True, hide_index=True)
        st.write("")

    if st.session_state.scan:
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
    else:
        st.info("Run a scan in Search to generate reports.")

    st.markdown("</div>", unsafe_allow_html=True)

st.write("")
st.caption("WeaveScope provides advisory risk signals and evidence outputs for community review. Not a legal determination.")
