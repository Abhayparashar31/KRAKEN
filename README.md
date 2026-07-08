![KRAKEN Banner](https://raw.githubusercontent.com/Abhayparashar31/KRAKEN/main/Banner_Image.png)

# 🐙 KRAKEN: OSINT Dork Generator

KRAKEN is a guided, wizard-style tool for building advanced search-engine and social-media
**dorks** — precise `site:`/`intitle:`/`filetype:`-style queries used for OSINT recon, content
discovery, and manual search refinement. Instead of memorizing operator syntax for every
engine and platform, KRAKEN walks you through a few simple questions and generates a full,
categorized set of ready-to-use queries, complete with clickable links.

> ⚠️ **For authorized research and public OSINT use only.** KRAKEN only *constructs search
> query strings* — it does not scrape, log in, bypass authentication, or access private data
> on any platform. Every generated query is meant to be run through a normal browser/search
> engine, and you are responsible for complying with the Terms of Service of whichever
> engine or platform you search against, and for only researching targets you are authorized
> to investigate.

---

## ✨ Features

- **Guided wizard flow** — enter a value, tell KRAKEN what type of parameter it is (name,
  username, email, phone, website, keyword), optionally add a date range, then choose which
  search engines and/or social platforms to generate dorks for.
- **Parameter-type awareness** — dorks adapt based on what you're searching for. A username
  triggers `@handle`/`from:`/`author:`-style operators; an email has its local-part extracted
  as a *probable* username (clearly labeled as a guess); a website switches everything to
  `site:`/`url:`-based queries instead of quoted free text.
- **Multi-engine, multi-platform** — generate dorks for several search engines and social
  platforms at once, or narrow down to just one.
- **Modular, self-contained architecture** — every search engine and social platform lives in
  its own file and owns its *entire* pipeline: the raw operator syntax **and** the final
  clickable URL. Adding a new one requires zero changes to the main app (see
  [`instructions.txt`](./instructions.txt)).
- **Categorized results** — dorks are grouped into tabs (General, Operators, File Mentions,
  Image, Video/Audio, Email, Password, Intitle, and platform-specific categories like People,
  Media, Engagement, etc.) instead of one long flat list.
- **Direct-to-source links for social platforms** — X and Reddit dorks open directly on
  `x.com/search` and `reddit.com/search`, not routed through a third-party search engine.
- **Extra keyword narrowing** — when targeting a social platform, optionally add comma-separated
  keywords that get AND-joined onto every dork generated for that platform.
- **Manual Dork Reference page** — a separate, persistent page with clickable cards for every
  supported engine/platform. Each card opens a modal with a static HTML reference (operators,
  filters, sample dorks, and use cases) for people who want to build dorks by hand.
- **Raw export** — download every generated dork as a plain `.txt` file (pure query strings,
  no labels or URLs — ready to paste anywhere).

---

## 🗂️ Project Structure

```
KRAKEN/
├── app.py                        # Main Streamlit wizard app
├── instructions.txt              # Module contract for adding new engines/platforms
├── requirements.txt
│
├── engines/                      # Search-engine modules (self-contained)
│   ├── __init__.py
│   ├── google.py
│   ├── duckduckgo.py
│   ├── yandex.py
│   ├── yahoo.py
│   ├── bing.py
│   └── startpage.py
│
├── platforms/                    # Social-platform modules (self-contained)
│   ├── __init__.py
│   ├── x.py
│   └── reddit.py
│
└── pages/                        # Streamlit multipage app
    ├── Dork_Reference.py
    └── templates/          # Static HTML reference content per source
        ├── google.html
        ├── duckduckgo.html
        ├── yandex.html
        ├── yahoo.html
        ├── bing.html
        ├── facebook.html
        ├── reddit.html
        └── x.html
```

---

## 🚀 Getting Started

### Requirements
- Python 3.9+
- pip

### Installation

```bash
git clone https://github.com/<your-username>/kraken.git
cd kraken
pip install -r requirements.txt
```

### Run

```bash
streamlit run app.py
```

Streamlit will open KRAKEN in your browser (default: `http://localhost:8501`). The **Manual
Dork Reference** page is available from the sidebar, or via the link at the bottom of the
main wizard page.

---

## 🧭 How to Use

1. **Enter a value** — a name, username, email, phone number, website, or keyword.
2. **Select the parameter type** — this changes how KRAKEN builds queries (e.g. a username
   gets `from:`/`author:` treatment; a website gets `site:`/`url:` treatment).
3. **(Optional) Add a date range** — restricts results where the engine/platform supports it.
4. **Choose whether to target social platforms** — select **None**, one, several, or **All**.
5. **Choose one or more search engines** to generate general-web dorks for.
6. **Review results** — grouped into tabs by category, each with the raw dork and a clickable
   link that opens the search directly.
7. **Download** the raw dork list as a `.txt` file if you want to save or share them.

---

![KRAKEN Test Image](https://raw.githubusercontent.com/Abhayparashar31/KRAKEN/main/Test_Image.png)

## 🧩 Adding a New Engine or Platform

KRAKEN is built so that adding support for a new search engine (e.g. Brave, Ecosia) or social
platform (e.g. Facebook, Instagram, LinkedIn) doesn't require touching `app.py` at all — it
auto-discovers every module dropped into `engines/` or `platforms/`.

See **[`instructions.txt`](./instructions.txt)** for the full contract each module must follow,
including required constants (`NAME` / `DOMAIN`, `DISPLAY_NAME`), the required
`generate_dorks(...)` function signature, and the expected return shape
(`dict[category] -> list[(label, raw_dork, full_url)]`).

In short:
```python
# engines/newengine.py
NAME = "NewEngine"

def generate_dorks(value, ptype, date_from=None, date_to=None):
    ...
    return {
        "General-Dorks": [(label, raw_dork, full_url), ...],
        ...
    }
```

Drop the file in, restart the app, and it appears automatically in the engine/platform
selector.

---

## 📚 Manual Dork Reference

Alongside the generator, KRAKEN ships a static reference page for people who prefer to write
dorks by hand. Each card (Google, DuckDuckGo, Yandex, Yahoo, Bing, Startpage, X, Reddit,
Facebook, Instagram) opens a modal rendering an HTML file from
`pages/dork_references/<slug>.html`. If a file doesn't exist yet for a given source, a generic
placeholder is shown instead — so you can fill these in one at a time without touching any
Python code.

---

## ⚠️ Responsible Use

KRAKEN is a **query-construction tool**, not a scraper, credential tester, or automation
framework. It does not:
- Access, store, or transmit anyone's private data
- Bypass logins, CAPTCHAs, rate limits, or authentication of any kind
- Automate account creation, scraping, or mass requests against any platform

You are responsible for:
- Only using generated dorks against targets you are authorized to research (yourself,
  consenting clients, or public information within legal and ethical bounds)
- Complying with the Terms of Service of every search engine and platform you query
- Complying with applicable laws in your jurisdiction regarding OSINT and data collection

---

## 🛣️ Roadmap

- [ ] Facebook dork module (people / photos / pages / places / posts / events)
- [ ] Instagram dork module (people / photos / pages / places / posts / tags / reels)
- [ ] Additional search engines (Brave, Ecosia, etc.)
- [ ] Subreddit-name and List-ID input fields (currently placeholder-based)
- [ ] Packaging as an installable CLI tool / Kali package

---

## 📄 License

*(Add your preferred license here — e.g. MIT, Apache 2.0 — before publishing.)*

## 🤝 Contributing

Contributions that add new engine/platform modules following the `instructions.txt` contract,
or that expand the Manual Dork Reference HTML content, are welcome. Please open an issue or
pull request describing the addition.