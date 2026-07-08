"""
KRAKEN: OSINT DORK GENERATOR
=============================
See instructions.txt for the engine/platform module contract.
Each engine module (engines/*.py) is fully self-contained: it builds
its OWN raw dorks and its OWN clickable URLs. app.py just displays
whatever each selected engine/platform module returns.
"""

import importlib
import pkgutil
from datetime import date
from urllib.parse import quote_plus

import streamlit as st

import engines as engines_pkg
import platforms as platforms_pkg

PARAM_TYPES = ["Person / Full Name", "Username / Handle", "Email Address",
               "Phone Number", "Website / Domain", "Generic Keyword"]


@st.cache_resource
def load_modules(package):
    modules = {}
    for _, modname, _ in pkgutil.iter_modules(package.__path__):
        mod = importlib.import_module(f"{package.__name__}.{modname}")
        modules[modname] = mod
    return modules


ENGINE_MODULES = load_modules(engines_pkg)
PLATFORM_MODULES = load_modules(platforms_pkg)

LOGO_DOMAIN = {
    "Google": "google.com",
    "DuckDuckGo": "duckduckgo.com",
    "Yandex": "yandex.com",
    "Yahoo": "yahoo.com",
    "Bing": "bing.com",
    "Startpage": "startpage.com",
    "X (Twitter)": "x.com",
    "Reddit": "reddit.com",
    "Facebook": "facebook.com",
    "Instagram": "instagram.com",
    "LinkedIn": "linkedin.com"
}


def logo_header(name: str, level: str = "##"):
    """Render a section header using the source's real favicon instead of an emoji."""
    domain = LOGO_DOMAIN.get(name)
    hashes = "#" * len(level) if level.startswith("#") else "##"
    if domain:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;margin:6px 0;">'
            f'<img src="https://www.google.com/s2/favicons?domain={domain}&sz=64" '
            f'width="26" style="border-radius:4px;">'
            f'<span style="font-size:1.4rem;font-weight:600;">{name}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(f"{hashes} {name}")


st.set_page_config(page_title="KRAKEN: OSINT DORKS GENERATOR", page_icon="🐙", layout="centered")

# Fix low-contrast tab scroll arrows when many tabs overflow the row
st.markdown("""
<style>
.stTabs [data-baseweb="tab-list"] {
    overflow-x: auto !important;
    gap: 4px;
}
.stTabs [data-baseweb="tab-list"] button[data-testid="stTabsSliderIndicator"] {
    background-color: #FF4B4B !important;
    height: 3px !important;
}
.stTabs button[kind="tabItem"] svg,
.stTabs [data-baseweb="tab-list"] > div svg {
    fill: currentColor !important;
    opacity: 1 !important;
}
.stTabs [data-baseweb="tab-border"] {
    background-color: rgba(128,128,128,0.35) !important;
}
/* Left/right scroll chevrons that appear when tabs overflow */
.stTabs [data-baseweb="tab-list"] + div button,
button[aria-label="scroll tabs left"],
button[aria-label="scroll tabs right"] {
    background-color: rgba(128,128,128,0.25) !important;
    border-radius: 6px !important;
    opacity: 1 !important;
}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<style>
/* Fix low-contrast tab scroll arrows / tab bar so category tabs
   (Date-Dorks, Operator-Dorks, etc.) are actually readable and the
   left/right scroll chevrons are visible when tabs overflow. */
button[data-baseweb="tab"] {
    font-size: 0.95rem !important;
    padding: 8px 14px !important;
    white-space: nowrap;
}
div[data-baseweb="tab-list"] {
    overflow-x: auto !important;
    scrollbar-width: thin;
    gap: 4px;
}
div[data-baseweb="tab-border"] { display: none; }
button[data-testid="stTabsScrollButton"] svg,
[data-baseweb="tab-list"] + div svg {
    color: #ffffff !important;
    opacity: 1 !important;
}
button[data-testid="stTabsScrollButton"] {
    background: rgba(120, 120, 120, 0.35) !important;
    border-radius: 6px !important;
}
</style>
""", unsafe_allow_html=True)

if "step" not in st.session_state:
    st.session_state.step = 1

def goto(step):
    st.session_state.step = step

st.title("🐙 KRAKEN: OSINT DORKS GENERATOR")
st.caption("Guided wizard for building advanced search dorks. For authorized research and public OSINT use only.")
st.progress({1: .16, 2: .33, 3: .5, 4: .66, 5: .83, 6: 1.0}.get(st.session_state.step, .1))
if st.session_state.step == 1:
    st.subheader("Step 1 — Enter your search parameter")
    value = st.text_input("What are you searching for?", value=st.session_state.get("value", ""),
                           placeholder="e.g. John Doe, john_doe99, john@example.com, +1-202-555-0143, example.com")
    if st.button("Next ➜", disabled=not value.strip()):
        st.session_state.value = value.strip()
        goto(2); st.rerun()

# ---- Step 2: parameter type ----
elif st.session_state.step == 2:
    st.subheader("Step 2 — What type of parameter is this?")
    ptype = st.radio("Select type:", PARAM_TYPES,
                      index=PARAM_TYPES.index(st.session_state.get("ptype", PARAM_TYPES[0])))
    c1, c2 = st.columns(2)
    if c1.button("⟵ Back"): goto(1); st.rerun()
    if c2.button("Next ➜"):
        st.session_state.ptype = ptype
        goto(3); st.rerun()

# ---- Step 3: date range ----
elif st.session_state.step == 3:
    st.subheader("Step 3 — Add a date range filter?")
    want_dr = st.radio("Restrict results to a date range?", ["No", "Yes"],
                        index=["No", "Yes"].index(st.session_state.get("want_dr", "No")))
    date_from, date_to = None, None
    if want_dr == "Yes":
        c1, c2 = st.columns(2)
        date_from = c1.date_input("From", value=st.session_state.get("date_from_obj", date(2015, 1, 1)))
        date_to = c2.date_input("To", value=st.session_state.get("date_to_obj", date.today()))
    c1, c2 = st.columns(2)
    if c1.button("⟵ Back"): goto(2); st.rerun()
    if c2.button("Next ➜"):
        st.session_state.want_dr = want_dr
        st.session_state.date_from = str(date_from) if date_from else None
        st.session_state.date_to = str(date_to) if date_to else None
        goto(4); st.rerun()

# ---- Step 4: target a platform? ----
elif st.session_state.step == 4:
    st.subheader("Step 4 — Search on specific social platform(s)?")
    want_platform = st.radio("Target specific social media platform(s)?",
                              ["No, general web only", "Yes"],
                              index=0 if st.session_state.get("want_platform", "No, general web only").startswith("No") else 1)
    c1, c2 = st.columns(2)
    if c1.button("⟵ Back"): goto(3); st.rerun()
    if c2.button("Next ➜"):
        st.session_state.want_platform = want_platform
        goto(5); st.rerun()

# ---- Step 5: platform + engine selection ----
elif st.session_state.step == 5:
    st.subheader("Step 5 — Choose platform(s) & search engine(s)")

    selected_platforms = []
    extra_keywords = []
    if st.session_state.want_platform == "Yes":
        available = {mod.DISPLAY_NAME: name for name, mod in PLATFORM_MODULES.items()}
        if not available:
            st.warning("No platform modules found in platforms/. Add one following instructions.txt.")
        options = list(available.keys()) + ["All"]
        choice = st.multiselect("Platform(s):", options,
                                 default=st.session_state.get("platform_choice_display", []))
        st.session_state.platform_choice_display = choice

        selected_platforms = list(PLATFORM_MODULES.keys()) if "All" in choice else [available[c] for c in choice]

        if selected_platforms:
            kw_raw = st.text_input("Extra keywords to narrow platform dorks (comma-separated, optional):",
                                    value=st.session_state.get("extra_keywords_raw", ""),
                                    placeholder="e.g. hiring, remote, portfolio")
            st.session_state.extra_keywords_raw = kw_raw
            extra_keywords = [k.strip() for k in kw_raw.split(",") if k.strip()]
    else:
        st.info("General web dorks only will be generated (no social platform selected).")

    st.markdown("---")
    engine_display_map = {mod.NAME: name for name, mod in ENGINE_MODULES.items()}
    engine_choice = st.multiselect("Search engine(s) — select one or more:",
                                    list(engine_display_map.keys()),
                                    default=st.session_state.get("engine_choice_display",
                                                                  list(engine_display_map.keys())))
    st.session_state.engine_choice_display = engine_choice
    selected_engines = [engine_display_map[e] for e in engine_choice]

    c1, c2 = st.columns(2)
    if c1.button("⟵ Back"): goto(4); st.rerun()
    if c2.button("Generate Dorks 🔍", disabled=not selected_engines):
        st.session_state.selected_platforms = selected_platforms
        st.session_state.selected_engines = selected_engines
        st.session_state.extra_keywords = extra_keywords
        goto(6); st.rerun()

# ---- Step 6: results ----
elif st.session_state.step == 6:
    st.subheader("Results")

    value = st.session_state.value
    ptype = st.session_state.ptype
    date_from = st.session_state.get("date_from") if st.session_state.want_dr == "Yes" else None
    date_to = st.session_state.get("date_to") if st.session_state.want_dr == "Yes" else None
    selected_platforms = st.session_state.get("selected_platforms", [])
    selected_engines = st.session_state.get("selected_engines", [])

    raw_dorks_for_download = []  # pure dork strings, no labels, no urls, deduped

    for ename in selected_engines:
        emod = ENGINE_MODULES[ename]
        logo_header(emod.NAME)
        categorized = emod.generate_dorks(value, ptype, date_from, date_to)

        category_labels = [c.replace("-", " ") for c in categorized.keys()]
        tabs = st.tabs(category_labels)

        for tab, (category, items) in zip(tabs, categorized.items()):
            with tab:
                st.caption(f"{len(items)} dorks in this category")
                for label, raw_dork, url in items:
                    with st.expander(label):
                        st.code(raw_dork, language="text")
                        st.markdown(f"[🔗 Open in {emod.NAME}]({url})")
                    if raw_dork not in raw_dorks_for_download:
                        raw_dorks_for_download.append(raw_dork)

        st.divider()

    # ---------------- Platform-specific dorks (open directly on the platform) ----------------
    extra_kw = st.session_state.get("extra_keywords", [])
    for pname in selected_platforms:
        pmod = PLATFORM_MODULES[pname]
        logo_header(pmod.DISPLAY_NAME)
        categorized = pmod.generate_dorks(value, ptype, date_from, date_to, extra_keywords=extra_kw)

        category_labels = [c.replace("-", " ") for c in categorized.keys()]
        tabs = st.tabs(category_labels)

        for tab, (category, items) in zip(tabs, categorized.items()):
            with tab:
                if not items:
                    st.caption("No dorks in this category for the current parameter type.")
                    continue
                st.caption(f"{len(items)} dorks in this category")
                for label, raw_dork, url in items:
                    with st.expander(label):
                        st.code(raw_dork, language="text")
                        st.markdown(f"[🔗 Open on {pmod.DISPLAY_NAME}]({url})")
                    if raw_dork not in raw_dorks_for_download:
                        raw_dorks_for_download.append(raw_dork)
        st.divider()

    # Pure raw dorks only - no titles, no headers, one per line
    st.download_button("⬇️ Download raw dorks (.txt)",
                        data="\n".join(raw_dorks_for_download),
                        file_name=f"kraken_{value.replace(' ', '_')}.txt",
                        mime="text/plain")

    st.divider()
    c1, c2 = st.columns(2)
    if c1.button("⟵ Back to platform/engine selection"): goto(5); st.rerun()
    if c2.button("🔁 Start Over"):
        for k in list(st.session_state.keys()):
            del st.session_state[k]
        goto(1); st.rerun()

    st.caption("⚠️ Use only against targets you are authorized to research, and respect each platform's "
               "and search engine's Terms of Service.")

# ================= PERSISTENT BOTTOM LINK (visible on every step) =================
st.markdown("---")
col1, col2 = st.columns(2)
with col1:
    st.page_link(
        "pages/Dork_Reference.py",
        label="📚 Dork References: Manual Search References",
    )

with col2:
    st.page_link(
        "https://start.me/p/xj5yzR/osint-tools",
        label="⚙️ My Personal OSINT Tools Glossary",
    )
