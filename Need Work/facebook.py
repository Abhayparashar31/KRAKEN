"""
platforms/facebook.py
========================
Self-contained dork generator for FACEBOOK.

URL STRATEGY (updated):
Facebook DOES expose real, type-scoped native search URLs:
    https://www.facebook.com/search/top/?q=TERM
    https://www.facebook.com/search/people/?q=TERM
    https://www.facebook.com/search/pages/?q=TERM
    https://www.facebook.com/search/photos/?q=TERM
    https://www.facebook.com/search/videos/?q=TERM
    https://www.facebook.com/search/places/?q=TERM
    https://www.facebook.com/search/groups/?q=TERM
    https://www.facebook.com/search/events/?q=TERM
Facebook's own search engine understands plain keyword queries against
these type-scoped endpoints - so every category below gets ONE native,
directly-clickable entry using the plain term against the matching
endpoint (and a direct https://facebook.com/<username> link when a
username/handle is known).

Facebook's search does NOT understand Google-style operators
(site:, inurl:, filetype:, intitle:, boolean grouping). Those deeper
recon dorks are still generated (tagged photos, permalink posts,
exposed documents, login/admin discovery, etc.) but have no native
URL - those get native_url=None and MUST be opened through a search
engine that has crawled facebook.com, which app.py handles by
wrapping them with whichever engine module the user selected.

(Note: Facebook increasingly requires being logged in to view full
search results, same as most social platforms today - the URL
structure itself is still public and legitimate, but results may be
partial or redirect to a login wall depending on your session state.)

PARAMETER-TYPE AWARENESS:
  - "Username / Handle"   -> treated as a Facebook vanity URL/username
                             (facebook.com/<username>).
  - "Email Address"       -> local-part before "@" extracted as a
                             PROBABLE username, labeled as a guess.
  - "Person / Full Name"  -> no username assumption; quoted free-text
                             search instead.
  - "Phone Number"        -> free-text phrase search only.
  - "Website / Domain"    -> not particularly meaningful for Facebook;
                             falls back to quoted free-text search of
                             the domain string itself.
  - "Generic Keyword"     -> quoted free-text search.

See instructions.txt for the full module contract.
"""
from urllib.parse import quote_plus

DOMAIN = "facebook.com"
DISPLAY_NAME = "Facebook"


def _j(*parts):
    return " ".join(p for p in parts if p and str(p).strip())


def _native(query_term, search_type="top"):
    return f"https://www.facebook.com/search/{search_type}/?q={quote_plus(query_term)}"


def _resolve_username(value, ptype):
    if ptype == "Username / Handle":
        return value.lstrip("@").strip(), False
    if ptype == "Email Address" and "@" in value:
        return value.split("@")[0].strip(), True
    return None, False


def generate_dorks(value, ptype, date_from=None, date_to=None, extra_keywords=None):
    """
    INPUT
    -----
    value, ptype, date_from, date_to : see module docstring
    extra_keywords : list[str] | None
                      Additional free-text keywords, AND-joined onto
                      every operator-based dork generated (native
                      search entries use the plain term only, since
                      Facebook's own search doesn't support AND-style
                      keyword stacking the way a dork operator does).

    OUTPUT
    ------
    dict[str, list[tuple[str, str, str | None]]]
        category -> [(label, raw_dork, native_url_or_None), ...]
        native_url is a real, directly-clickable Facebook URL when one
        exists for that specific dork; None means this dork needs a
        search engine (app.py wraps it with the user's selected engine).
    """
    extra_keywords = [k.strip() for k in (extra_keywords or []) if k.strip()]
    extra_clause = " ".join(f'"{k}"' if " " in k else k for k in extra_keywords)

    username, guessed = _resolve_username(value, ptype)
    quoted = f'"{value}"'
    fb = "site:facebook.com"

    dr = ""
    if date_from:
        dr = _j(dr, f"after:{date_from}")
    if date_to:
        dr = _j(dr, f"before:{date_to}")

    sections = {}

    # ================= PEOPLE =================
    people = []
    if username:
        note = " (guessed from email)" if guessed else ""
        people.append((f"Direct profile{note}", f"facebook.com/{username}", f"https://www.facebook.com/{username}"))
    people.append(("Native people search", value, _native(value, "people")))
    if username:
        note = " (guessed from email)" if guessed else ""
        people += [
            (f"Profile via profile.php lookup{note}", _j(fb, "inurl:profile.php", f'"{username}"', dr), None),
            (f"About/work & education info{note}", _j(fb, f'"{username}"', '("works at" OR "studied at" OR "lives in")', dr), None),
        ]
    else:
        people += [
            ("Profile pages matching a name (operator)", _j(fb, "inurl:profile.php", quoted, dr), None),
            ("Vanity-URL profiles (operator)", _j(fb, quoted, "-inurl:pages", "-inurl:groups", extra_clause, dr), None),
            ("About/work & education info (operator)", _j(fb, quoted, '("works at" OR "studied at" OR "lives in")', dr), None),
        ]
    sections["People-Dorks"] = people

    # ================= PHOTOS =================
    sections["Photo-Dorks"] = [
        ("Native photo search", value, _native(value, "photos")),
        ("Photos mentioning the target (operator)", _j(fb, "inurl:photo", quoted, extra_clause, dr), None),
        ("Tagged photos (operator)", _j(fb, quoted, '"tagged in"', extra_clause, dr), None),
        ("Photo albums (operator)", _j(fb, "inurl:media/set", quoted, extra_clause, dr), None),
    ]

    # ================= PAGES =================
    sections["Page-Dorks"] = [
        ("Native pages search", value, _native(value, "pages")),
        ("Business/brand pages (operator)", _j(fb, quoted, '("Page" OR "Official Page")', extra_clause, dr), None),
        ("Verified pages (operator)", _j(fb, quoted, '"Verified Page"', dr), None),
    ]

    # ================= PLACES =================
    sections["Place-Dorks"] = [
        ("Native places search", value, _native(value, "places")),
        ("Location-tagged content (operator)", _j(fb, quoted, '"checked in at"', extra_clause, dr), None),
    ]

    # ================= POSTS =================
    sections["Post-Dorks"] = [
        ("Native posts search", value, _native(value, "top")),
        ("Public posts mentioning the target (operator)", _j(fb, "inurl:posts", quoted, extra_clause, dr), None),
        ("Permalink-style posts (operator)", _j(fb, "inurl:permalink", quoted, extra_clause, dr), None),
    ]

    # ================= EVENTS =================
    sections["Event-Dorks"] = [
        ("Native events search", value, _native(value, "events")),
        ("Events with a location hint (operator)", _j(fb, "inurl:events", quoted, '"at"', extra_clause, dr), None),
    ]

    # ================= GROUPS =================
    sections["Group-Dorks"] = [
        ("Native groups search", value, _native(value, "groups")),
        ("Group discussion mentioning target (operator)", _j(fb, "inurl:groups", quoted, "inurl:permalink", dr), None),
    ]

    # ================= VIDEOS =================
    sections["Video-Dorks"] = [
        ("Native videos search", value, _native(value, "videos")),
        ("Watch-page videos (operator)", _j(fb, "inurl:watch", quoted, extra_clause, dr), None),
    ]

    # ================= FILE / DOCUMENT MENTIONS (operator-only, no native equivalent) =================
    sections["File-Mentions"] = [
        ("PDF documents shared/linked", _j(fb, quoted, "filetype:pdf", dr), None),
        ("Spreadsheet mentions", _j(fb, quoted, "(filetype:xlsx OR filetype:csv)", dr), None),
    ]

    # ================= ADVANCED OPERATORS (operator-only) =================
    sections["Operator-Dorks"] = [
        ('"phrase" - exact phrase', _j(fb, quoted, extra_clause, dr), None),
        ("OR - either term", _j(fb, f'({quoted} OR "{value} profile")', extra_clause, dr), None),
        ("- (exclude) - remove noisy result types", _j(fb, quoted, "-inurl:pages", "-inurl:groups", dr), None),
        ("() (grouping) - combined logic", _j(fb, f'({quoted})', "(inurl:posts OR inurl:photo)", dr), None),
    ]

    # ---- normalize + dedupe ----
    final = {}
    for category, items in sections.items():
        seen = set()
        deduped = []
        for label, raw, url in items:
            raw = " ".join(raw.split())
            if not raw.strip() or raw in seen:
                continue
            seen.add(raw)
            deduped.append((label, raw, url))
        final[category] = deduped

    return final