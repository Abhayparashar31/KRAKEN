"""
platforms/x.py
================
Self-contained dork generator for X (formerly Twitter).

Unlike search-engine modules, X dorks open DIRECTLY on x.com/search -
never routed through Google/Bing/etc. This module owns both the raw
query syntax (X's own advanced-search operators) and the final
browsable URL.

Reference: X's advanced search operators as used by the public
x.com/search web UI (from:, to:, filter:, since:, until:, min_faves,
near:, url:, etc.) - overlapping with, but not identical to, the
X API v2 operator set (has:/is:) documented at
https://docs.x.com/x-api/posts/search/integrate/operators

PARAMETER-TYPE AWARENESS (this is the important part):
  - "Username / Handle"   -> value is treated as an @handle. Dorks lean
                             on from:/to:/@mention which only make
                             sense for a known handle.
  - "Email Address"       -> the local-part before "@" is extracted as
                             a PROBABLE username (e.g. john.doe@x.com
                             -> "john.doe") and used the same way a
                             handle would be, clearly labeled as a
                             guess since emails don't map 1:1 to
                             X handles.
  - "Person / Full Name"  -> no handle assumption; dorks use quoted
                             free-text search instead of from:/to:.
  - "Phone Number"        -> free-text phrase search only (X search
                             has no phone-specific operator).
  - "Website / Domain"    -> leans on url: operator instead of
                             quoted free text.
  - "Generic Keyword"     -> quoted free-text search.

See instructions.txt for the full module contract.
"""
from urllib.parse import quote_plus

DOMAIN = "x.com"
DISPLAY_NAME = "X (Twitter)"

BASE_SEARCH = "https://x.com/search"


def _j(*parts):
    return " ".join(p for p in parts if p and str(p).strip())


def _url(query, mode="live"):
    """mode: 'live' (Latest tab), 'top' (Top tab), 'user' (People tab)."""
    f_param = {"live": "live", "top": "top", "user": "user"}.get(mode, "live")
    return f"{BASE_SEARCH}?q={quote_plus(query)}&src=typed_query&f={f_param}"


def _resolve_handle(value, ptype):
    """Return (handle_or_None, is_guessed_bool)."""
    if ptype == "Username / Handle":
        return value.lstrip("@").strip(), False
    if ptype == "Email Address" and "@" in value:
        return value.split("@")[0].strip(), True
    return None, False


def generate_dorks(value, ptype, date_from=None, date_to=None, extra_keywords=None):
    """
    INPUT
    -----
    value          : str   raw parameter value
    ptype          : str   one of app.py's PARAM_TYPES
    date_from      : str | None   "YYYY-MM-DD"
    date_to        : str | None   "YYYY-MM-DD"
    extra_keywords : list[str] | None
                     Additional free-text keywords the user optionally
                     supplied in the UI to narrow every dork down
                     further (AND-joined onto every query generated).

    OUTPUT
    ------
    dict[str, list[tuple[str, str, str]]]
        category -> [(label, raw_dork, full_url), ...]
        Every full_url points directly at x.com/search - never at a
        third-party search engine.
    """
    extra_keywords = [k.strip() for k in (extra_keywords or []) if k.strip()]
    extra_clause = " ".join(f'"{k}"' if " " in k else k for k in extra_keywords)

    handle, guessed = _resolve_handle(value, ptype)
    is_website = ptype == "Website / Domain"
    domain = value.replace("https://", "").replace("http://", "").strip("/") if is_website else None

    dr = ""
    if date_from:
        dr = _j(dr, f"since:{date_from}")
    if date_to:
        dr = _j(dr, f"until:{date_to}")

    quoted = f'"{value}"' if not is_website else None

    sections = {}

    # ================= PEOPLE DORKS (only meaningful with a handle) =================
    people = []
    if handle:
        note = " (guessed from email)" if guessed else ""
        people += [
            (f"Posts by @{handle}{note}", _j(f"from:{handle}", extra_clause, dr)),
            (f"Replies to @{handle}{note}", _j(f"to:{handle}", extra_clause, dr)),
            (f"Mentions of @{handle}{note}", _j(f"@{handle}", extra_clause, dr)),
            (f"Media posted by @{handle}{note}", _j(f"from:{handle}", "filter:media", extra_clause, dr)),
            (f"Links shared by @{handle}{note}", _j(f"from:{handle}", "filter:links", extra_clause, dr)),
            (f"Original posts (no replies) by @{handle}{note}", _j(f"from:{handle}", "-filter:replies", extra_clause, dr)),
            (f"Verified mentions of @{handle}{note}", _j(f"@{handle}", "filter:verified", extra_clause, dr)),
        ]
    elif ptype in ("Person / Full Name", "Generic Keyword"):
        people.append(("Possible verified profile mentions", _j(quoted, "filter:verified", extra_clause, dr)))
    sections["People-Dorks"] = people

    # ================= POST / KEYWORD DORKS =================
    base_term = f'url:"{domain}"' if is_website else quoted
    posts = [
        ("Exact phrase mention", _j(base_term, extra_clause, dr)),
        ("Excluding retweets/replies noise", _j(base_term, "-filter:replies", extra_clause, dr)),
        ("News-flagged posts", _j(base_term, "filter:news", extra_clause, dr)),
        ("Safe-content filtered", _j(base_term, "filter:safe", extra_clause, dr)),
    ]
    sections["Post-Dorks"] = posts

    # ================= MEDIA DORKS =================
    sections["Media-Dorks"] = [
        ("Any media (photo/GIF/video)", _j(base_term, "filter:media", extra_clause, dr)),
        ("Images only", _j(base_term, "filter:images", extra_clause, dr)),
        ("Videos only", _j(base_term, "filter:videos", extra_clause, dr)),
        ("Native X video only", _j(base_term, "filter:native_video", extra_clause, dr)),
        ("Periscope/broadcast mentions", _j(base_term, "filter:periscope", extra_clause, dr)),
    ]

    # ================= URL DORKS =================
    if is_website:
        url_dorks = [
            ("Links to this domain", _j(f'url:"{domain}"', extra_clause, dr)),
            ("Links to this domain + media", _j(f'url:"{domain}"', "filter:media", extra_clause, dr)),
            ("Links to this domain, excluding replies", _j(f'url:"{domain}"', "-filter:replies", extra_clause, dr)),
        ]
    else:
        url_dorks = [("Posts containing any link + this term", _j(quoted, "filter:links", extra_clause, dr))]
    sections["URL-Dorks"] = url_dorks

    # ================= HASHTAG / MENTION DORKS =================
    tag_term = value.replace(" ", "") if value else value
    hashtag_dorks = [
        (f"Hashtag #{tag_term}", _j(f"#{tag_term}", extra_clause, dr)),
    ]
    if handle:
        hashtag_dorks.append((f"Cashtag-style lookup ${handle}", _j(f"${handle}", extra_clause, dr)))
    sections["Hashtag-Mention-Dorks"] = hashtag_dorks

    # ================= ENGAGEMENT DORKS =================
    sections["Engagement-Dorks"] = [
        ("Highly liked posts (100+ likes)", _j(base_term, "min_faves:100", extra_clause, dr)),
        ("Highly retweeted posts (50+ RTs)", _j(base_term, "min_retweets:50", extra_clause, dr)),
        ("Highly replied posts (20+ replies)", _j(base_term, "min_replies:20", extra_clause, dr)),
        ("Viral posts (combined thresholds)", _j(base_term, "min_faves:500", "min_retweets:100", extra_clause, dr)),
    ]

    # ================= LOCATION DORKS (template - user fills in) =================
    sections["Location-Dorks"] = [
        ("Near a city (edit CITY placeholder)", _j(base_term, 'near:"CITY"', "within:15mi", extra_clause, dr)),
    ]

    # ================= DATE DORKS =================
    date_dorks = []
    if date_from or date_to:
        date_dorks.append(("Within selected date range", _j(base_term, dr, extra_clause)))
    date_dorks.append(("Last 24 hours (edit dates)", _j(base_term, "since:2026-07-07", "until:2026-07-08", extra_clause)))
    sections["Date-Dorks"] = date_dorks

    # ================= ADVANCED OPERATORS =================
    first_kw = value.split()[0] if value.split() else value
    sections["Operator-Dorks"] = [
        ('"phrase" - exact phrase', _j(quoted or f'url:"{domain}"', extra_clause, dr)),
        ("OR - either term", _j(f'({base_term} OR "{value} update")', extra_clause, dr)),
        ("- (exclude) - remove a term", _j(base_term, f"-{first_kw}spam", extra_clause, dr)),
        ("() (grouping) - combined logic", _j(f'({base_term}) filter:media -filter:replies', extra_clause, dr)),
        ("list: - posts from a specific List (edit LIST_ID)", "list:LIST_ID " + (extra_clause or "")),
    ]

    final = {}
    for category, items in sections.items():
        seen = set()
        deduped = []
        for label, raw in items:
            raw = " ".join(raw.split())
            if not raw.strip() or raw in seen:
                continue
            seen.add(raw)
            mode = "user" if category == "People-Dorks" and handle else "live"
            deduped.append((label, raw, _url(raw, mode)))
        final[category] = deduped

    return final