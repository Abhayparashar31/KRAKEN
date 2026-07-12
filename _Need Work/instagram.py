"""
platforms/instagram.py
=========================
Self-contained dork generator for INSTAGRAM.

URL STRATEGY (updated):
Instagram has a much smaller set of real, structurally-defined public
URLs than Facebook - no type-scoped search-by-category endpoints.
What genuinely works:
    https://www.instagram.com/<username>/                (direct profile)
    https://www.instagram.com/explore/tags/<tag>/         (hashtag page)
    https://www.instagram.com/explore/search/keyword/?q=  (keyword search -
        the same URL Instagram's own web UI navigates to when you type
        into its search bar; works for plain keyword terms)
Everything else (bio-text search, tagged-photo search, filtered post
search, file mentions, etc.) has no native Instagram endpoint at all -
those dorks keep Google-style site:instagram.com operators and get
native_url=None, meaning app.py must wrap them with a selected search
engine to be clickable.

PARAMETER-TYPE AWARENESS:
  - "Username / Handle"   -> treated as an Instagram @handle
                             (instagram.com/<username>).
  - "Email Address"       -> local-part before "@" extracted as a
                             PROBABLE username, labeled as a guess.
  - "Person / Full Name"  -> no username assumption; quoted free-text
                             search instead.
  - "Phone Number"        -> free-text phrase search only.
  - "Website / Domain"    -> not particularly meaningful for Instagram;
                             falls back to quoted free-text search of
                             the domain string.
  - "Generic Keyword"     -> quoted free-text search, also used to
                             build a hashtag-style dork.

See instructions.txt for the full module contract.
"""
from urllib.parse import quote_plus

DOMAIN = "instagram.com"
DISPLAY_NAME = "Instagram"


def _j(*parts):
    return " ".join(p for p in parts if p and str(p).strip())


def _profile_url(username):
    return f"https://www.instagram.com/{username}/"


def _tag_url(tag):
    return f"https://www.instagram.com/explore/tags/{tag}/"


def _keyword_search_url(term):
    return f"https://www.instagram.com/explore/search/keyword/?q={quote_plus(term)}"


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
                      every operator-based dork generated.

    OUTPUT
    ------
    dict[str, list[tuple[str, str, str | None]]]
        category -> [(label, raw_dork, native_url_or_None), ...]
        native_url is a real, directly-clickable Instagram URL when one
        exists for that specific dork; None means this dork needs a
        search engine (app.py wraps it with the user's selected engine).
    """
    extra_keywords = [k.strip() for k in (extra_keywords or []) if k.strip()]
    extra_clause = " ".join(f'"{k}"' if " " in k else k for k in extra_keywords)

    username, guessed = _resolve_username(value, ptype)
    quoted = f'"{value}"'
    ig = "site:instagram.com"

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
        people.append((f"Direct profile{note}", f"instagram.com/{username}", _profile_url(username)))
        people += [
            (f"Bio/about mentions (operator){note}", _j(ig, f'"{username}"', '("bio" OR "about")', dr), None),
            (f"Mentions of this profile elsewhere (operator){note}", _j(ig, f'"{value}"', extra_clause, dr), None),
        ]
    else:
        people.append(("Native keyword search", value, _keyword_search_url(value)))
        people += [
            ("Profile pages matching a name (operator)", _j(ig, quoted, "-inurl:explore", "-inurl:p/", extra_clause, dr), None),
            ("Bio/about mentions matching a name (operator)", _j(ig, quoted, '("bio" OR "about")', dr), None),
        ]
    sections["People-Dorks"] = people

    # ================= PHOTOS (no native photo-only search - operator only) =================
    photos = []
    if username:
        photos.append((f"Posts (photos) by @{username} (operator)", _j(ig, "inurl:/p/", f'"{username}"', extra_clause, dr), None))
    photos += [
        ("Posts (photos) mentioning the target (operator)", _j(ig, "inurl:/p/", quoted, extra_clause, dr), None),
        ("Carousel/multi-photo posts (operator)", _j(ig, "inurl:/p/", quoted, '"photos"', dr), None),
    ]
    sections["Photo-Dorks"] = photos

    # ================= PAGES (business/brand accounts - operator only) =================
    sections["Page-Dorks"] = [
        ("Business/brand accounts (operator)", _j(ig, quoted, '("Official" OR "Business")', extra_clause, dr), None),
        ("Verified accounts (operator)", _j(ig, quoted, '"Verified"', dr), None),
        ("Contact info in bio (operator)", _j(ig, quoted, '("Contact" OR "Email" OR "Business Inquiries")', dr), None),
    ]

    # ================= PLACES (no native location-name search - operator only) =================
    sections["Place-Dorks"] = [
        ("Location-tagged posts (operator)", _j(ig, "inurl:/explore/locations", quoted, extra_clause, dr), None),
        ("Posts mentioning a check-in style location (operator)", _j(ig, quoted, '"at"', dr), None),
    ]

    # ================= POSTS =================
    posts = [("Native keyword search", value, _keyword_search_url(value))]
    if username:
        posts.append((f"All posts by @{username} (operator)", _j(ig, "inurl:/p/", f'"{username}"', extra_clause, dr), None))
    posts.append(("General posts mentioning the target (operator)", _j(ig, "inurl:/p/", quoted, extra_clause, dr), None))
    sections["Post-Dorks"] = posts

    # ================= TAGS =================
    tag_term = value.replace(" ", "") if value else value
    sections["Tag-Dorks"] = [
        (f"Native hashtag page #{tag_term}", f"#{tag_term}", _tag_url(tag_term)),
        ("Posts using a related hashtag (operator)", _j(ig, "inurl:/explore/tags", quoted, extra_clause, dr), None),
    ]

    # ================= REELS (no native reels-only search - operator only) =================
    reels = []
    if username:
        reels.append((f"Reels by @{username} (operator)", _j(ig, "inurl:/reel/", f'"{username}"', extra_clause, dr), None))
    reels.append(("Reels mentioning the target (operator)", _j(ig, "inurl:/reel/", quoted, extra_clause, dr), None))
    sections["Reel-Dorks"] = reels

    # ================= ADVANCED OPERATORS (operator-only) =================
    sections["Operator-Dorks"] = [
        ('"phrase" - exact phrase', _j(ig, quoted, extra_clause, dr), None),
        ("OR - either term", _j(ig, f'({quoted} OR "{value} official")', extra_clause, dr), None),
        ("- (exclude) - remove noisy result types", _j(ig, quoted, "-inurl:explore", "-inurl:reel", dr), None),
        ("() (grouping) - combined logic", _j(ig, f'({quoted})', "(inurl:/p/ OR inurl:/reel/)", dr), None),
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