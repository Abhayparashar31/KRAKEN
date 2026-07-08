"""
pages/1_Manual_Dork_Reference.py
====================================
A static reference page (separate from the wizard flow) listing cards
for every search engine and social platform. Clicking a card opens a
modal containing an HTML panel meant to hold raw operator/keyword
reference material for that source - for people who want to build
dorks by hand instead of using the generator.

CONTENT SOURCE
--------------
Each card looks for an external HTML file at:
    pages/dork_references/<slug>.html
(slug = card name, lowercased, spaces/parens stripped - see SLUG_MAP)

If that file exists, its content is shown as-is. If it doesn't exist
yet, a generic placeholder is shown instead. This means you can drop
in real reference content one file at a time without touching this
script - e.g. pages/dork_references/google.html is already provided
as a starting example; add reddit.html, x.html, facebook.html, etc.
whenever you're ready.
"""

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Dork References - KRAKEN", page_icon="📚", layout="wide")

REFERENCES_DIR = Path(__file__).parent / "templates"

CARDS = [
    {"name": "Google", "kind": "Search Engine", "domain": "google.com"},
    {"name": "DuckDuckGo", "kind": "Search Engine", "domain": "duckduckgo.com"},
    {"name": "Yandex", "kind": "Search Engine", "domain": "yandex.com"},
    {"name": "Yahoo", "kind": "Search Engine", "domain": "yahoo.com"},
    {"name": "Bing", "kind": "Search Engine", "domain": "bing.com"},
    # {"name": "Startpage", "kind": "Search Engine", "domain": "startpage.com"},
    {"name": "X (Twitter)", "kind": "Social Platform", "domain": "x.com"},
    {"name": "Reddit", "kind": "Social Platform", "domain": "reddit.com"},
    {"name": "Facebook", "kind": "Social Platform", "domain": "facebook.com"},
    {"name": "Instagram", "kind": "Social Platform", "domain": "instagram.com"},
]

SLUG_MAP = {
    "Google": "google",
    "DuckDuckGo": "duckduckgo",
    "Yandex": "yandex",
    "Yahoo": "yahoo",
    "Bing": "bing",
    #"Startpage": "startpage",
    "X (Twitter)": "x",
    "Reddit": "reddit",
    "Facebook": "facebook",
    "Instagram": "instagram",
}


def placeholder_html(name: str) -> str:
    """Shown only when pages/dork_references/<slug>.html doesn't exist yet."""
    return f"""
    <html>
      <head>
        <style>
          body {{
            font-family: -apple-system, Segoe UI, Roboto, sans-serif;
            padding: 24px;
            color: #222;
            background: #fafafa;
          }}
          h2 {{ margin-top: 0; }}
          code {{
            background: #eee;
            padding: 2px 6px;
            border-radius: 4px;
          }}
          .op-row {{
            display: flex;
            justify-content: space-between;
            border-bottom: 1px solid #ddd;
            padding: 8px 0;
          }}
        </style>
      </head>
      <body>
        <h2>{name} — Manual Dork Reference</h2>
        <p>No custom reference file found yet for <b>{name}</b>. Create
        <code>pages/dork_references/{SLUG_MAP.get(name, name.lower())}.html</code>
        and it will automatically replace this placeholder.</p>
        <div class="op-row"><span><code>example:operator</code></span><span>What it does</span></div>
        <div class="op-row"><span><code>"exact phrase"</code></span><span>Matches the exact phrase</span></div>
        <div class="op-row"><span><code>-exclude</code></span><span>Excludes a term from results</span></div>
      </body>
    </html>
    """


def load_reference_html(name: str) -> str:
    slug = SLUG_MAP.get(name, name.lower())
    filepath = REFERENCES_DIR / f"{slug}.html"
    if filepath.exists():
        return filepath.read_text(encoding="utf-8")
    return placeholder_html(name)


@st.dialog("Dork Reference", width="large")
def show_card(name: str):
    domain = next((c["domain"] for c in CARDS if c["name"] == name), None)
    if domain:
        st.markdown(
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">'
            f'<img src="https://www.google.com/s2/favicons?domain={domain}&sz=64" width="28" style="border-radius:4px;">'
            f'<span style="font-size:1.3rem;font-weight:600;">{name}</span></div>',
            unsafe_allow_html=True,
        )
    html = load_reference_html(name)
    components.html(html, height=700, scrolling=True)
    st.caption("Static reference only - nothing here is generated automatically.")


st.title("📚 Dork References")
st.caption("Browse raw operators, keywords, and search info per source to build your own dorks by hand, "
           "without using the generator wizard.")

st.divider()

cols_per_row = 4
rows = [CARDS[i:i + cols_per_row] for i in range(0, len(CARDS), cols_per_row)]
for row in rows:
    cols = st.columns(cols_per_row)
    for col, card in zip(cols, row):
        with col:
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:8px;">'
                f'<img src="https://www.google.com/s2/favicons?domain={card["domain"]}&sz=64" '
                f'width="22" style="border-radius:4px;"><b>{card["name"]}</b></div>',
                unsafe_allow_html=True,
            )
            st.caption(card["kind"])
            if st.button("Open reference", key=f"card_{card['name']}", use_container_width=True):
                show_card(card["name"])
            st.markdown("---")

st.info("💡 This page is separate from the wizard - use the sidebar, or the link at the bottom of the "
        "generator page, to jump back to **KRAKEN** at any time.")