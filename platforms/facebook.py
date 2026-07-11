"""
platforms/facebook.py
========================
Self-contained dork generator for FACEBOOK - native search edition.

Unlike the earlier site:facebook.com approach, this module builds
REAL, directly-clickable Facebook search URLs using Facebook's own
(undocumented but long-observed and widely-referenced) search filter
system: https://www.facebook.com/search/<type>/?q=<term>&filters=<b64>

Reference: this filter/base64 scheme is documented publicly at
  https://sowsearch.info/  (open-source Facebook search URL builder)
  https://gist.github.com/nemec/2ba8afa589032f20e2d6509512381114
Both have been maintained and referenced by OSINT researchers/
journalists for years. The `filters` param is base64(JSON), where each
key maps to a small JSON blob describing one filter, e.g. the "public
posts" filter used in this module's default Post/Photo/Video/Top
searches decodes to:
    {"rp_author": "{\"name\":\"merged_public_posts\",\"args\":\"\"}"}

IMPORTANT LIMITS - read before extending this module:
  - Only PUBLIC content is searchable this way - the same posts,
    pages, photos, and profiles Facebook's own search bar would
    surface to a logged-in user. This does not access anything
    private, friends-only, or behind Facebook's authentication wall.
  - Facebook changes/restricts this system periodically without
    notice - some filters have been reported to stop working after
    Facebook updates (see the gist's comment history). Treat these
    as "known to have worked" rather than "guaranteed to work".
  - Several filters (users_school, users_employer, users_location)
    require a Facebook-internal numeric ID, not a free-text name -
    those dorks use an ID_PLACEHOLDER you must replace by first
    finding the correct ID (e.g. via a plain people-search, then
    inspecting the resulting page/profile URL).
  - DELIBERATELY NOT IMPLEMENTED: the "Friends with" / mutual-friends
    filter documented in the sources above. Unlike public post/page/
    photo search, that filter exists specifically to reconstruct a
    person's friends list when they've set it to private - a genuine
    privacy-circumvention use case, not public-content discovery.
    This module does not generate that filter.

PARAMETER-TYPE AWARENESS:
  - "Username / Handle"   -> treated as a Facebook vanity URL/username
                             (facebook.com/<username>).
  - "Email Address"       -> local-part before "@" extracted as a
                             PROBABLE username, labeled as a guess.
  - "Person / Full Name"  -> no username assumption; quoted free-text
                             search instead.
  - "Phone Number"        -> free-text phrase search only.
  - "Website / Domain"    -> falls back to quoted free-text search of
                             the domain string itself.
  - "Generic Keyword"     -> quoted free-text search.

See instructions.txt for the full module contract.
"""
import base64
import json
from urllib.parse import quote_plus

DOMAIN = "facebook.com"
DISPLAY_NAME = "Facebook"

ID_PLACEHOLDER = "PAGE_OR_ENTITY_ID"


def _j(*parts):
    return " ".join(p for p in parts if p and str(p).strip())


def _encode_filters(filter_dict):
    """base64(JSON) - matches Facebook's own filters= encoding exactly."""
    compact = json.dumps(filter_dict, separators=(",", ":"))
    b64 = base64.b64encode(compact.encode()).decode()
    return b64.rstrip("=")  # Facebook doesn't need padding


def _search_url(term, search_type="top", filters=None):
    url = f"https://www.facebook.com/search/{search_type}/?q={quote_plus(term)}"
    if filters:
        url += f"&epa=FILTERS&filters={_encode_filters(filters)}"
    return url


def _resolve_username(value, ptype):
    if ptype == "Username / Handle":
        return value.lstrip("@").strip(), False
    if ptype == "Email Address" and "@" in value:
        return value.split("@")[0].strip(), True
    return None, False


# ---- reusable filter blobs (verified against the reference sources) ----
def _f_public_posts():
    return {"rp_author": json.dumps({"name": "merged_public_posts", "args": ""})}


def _f_chronological():
    return {"rp_chrono_sort": json.dumps({"name": "chronosort", "args": ""})}


def _f_author_page(page_id):
    return {"rp_author": json.dumps({"name": "author", "args": page_id})}


def _f_tagged_location(location_id):
    return {"rp_location": json.dumps({"name": "location", "args": location_id})}


def _f_date_range(start_year, end_year):
    args = json.dumps({
        "start_year": str(start_year), "start_month": f"{start_year}-1", "start_day": f"{start_year}-1-1",
        "end_year": str(end_year), "end_month": f"{end_year}-12", "end_day": f"{end_year}-12-31",
    })
    return {"rp_creation_time": json.dumps({"name": "creation_time", "args": args})}


def _f_pages_verified():
    return {"verified": json.dumps({"name": "pages_verified", "args": ""})}


PAGE_CATEGORIES = {
    "Local Business or Place": "1006",
    "Company/Organization/Institution": "1013",
    "Brand or Product": "1009",
    "Entertainment": "1019",
}


def _f_pages_category(label):
    return {"category": json.dumps({"name": "pages_category", "args": PAGE_CATEGORIES[label]})}


def _f_video_source(source):
    # source: "videos_live" | "videos_episode" | "videos_feed"
    return {"videos_source": json.dumps({"name": source, "args": ""})}


def generate_dorks(value, ptype, date_from=None, date_to=None, extra_keywords=None):
    """
    INPUT
    -----
    value, ptype, date_from, date_to : see module docstring.
                                        date_from/date_to are ISO dates;
                                        only the YEAR is used, since
                                        Facebook's date filter here
                                        operates on year granularity.
    extra_keywords : list[str] | None
                      Appended to the free-text `q=` term (Facebook's
                      own search doesn't support AND/OR the way a
                      search-engine dork does, so these are simply
                      joined into one search phrase).

    OUTPUT
    ------
    dict[str, list[tuple[str, str, str]]]
        category -> [(label, raw_dork, native_url), ...]
        raw_dork here is the human-readable query description (since
        the "real" query is embedded in the URL's filters param, not
        a plain text string like a search-engine dork).
    """
    extra_keywords = [k.strip() for k in (extra_keywords or []) if k.strip()]
    term = " ".join([value] + extra_keywords) if extra_keywords else value

    username, guessed = _resolve_username(value, ptype)

    year_from = date_from[:4] if date_from else None
    year_to = date_to[:4] if date_to else None

    sections = {}

    # ================= PEOPLE =================
    people = []
    if username:
        note = " (guessed from email)" if guessed else ""
        people.append((f"Direct profile{note}", f"facebook.com/{username}", f"https://www.facebook.com/{username}"))
    people.append(("People search (plain)", f'q="{term}", type=people', _search_url(term, "people")))
    people.append((
        "People search filtered by city (edit ID_PLACEHOLDER)",
        f'q="{term}", city=ID_PLACEHOLDER',
        _search_url(term, "people", {"city": json.dumps({"name": "users_location", "args": ID_PLACEHOLDER})}),
    ))
    people.append((
        "People search filtered by employer (edit ID_PLACEHOLDER)",
        f'q="{term}", employer=ID_PLACEHOLDER',
        _search_url(term, "people", {"employer": json.dumps({"name": "users_employer", "args": ID_PLACEHOLDER})}),
    ))
    sections["People-Dorks"] = people

    # ================= POSTS =================
    posts = [
        ("Public posts (most relevant)", f'q="{term}", public posts', _search_url(term, "posts", _f_public_posts())),
        ("Public posts, most recent first", f'q="{term}", public posts, chronological',
         _search_url(term, "posts", {**_f_public_posts(), **_f_chronological()})),
        ("Posts from a specific page/user (edit ID_PLACEHOLDER)", f'q="{term}", author={ID_PLACEHOLDER}',
         _search_url(term, "posts", _f_author_page(ID_PLACEHOLDER))),
    ]
    if year_from or year_to:
        y1, y2 = year_from or year_to, year_to or year_from
        posts.append((f"Public posts within {y1}-{y2}", f'q="{term}", date {y1}-{y2}',
                      _search_url(term, "posts", {**_f_public_posts(), **_f_date_range(y1, y2)})))
    sections["Post-Dorks"] = posts

    # ================= TOP (mixed results, chronological available) =================
    sections["Top-Dorks"] = [
        ("Top results (default relevance)", f'q="{term}"', _search_url(term, "top")),
        ("Top results, public posts, most recent", f'q="{term}", public posts, chronological',
         _search_url(term, "top", {**_f_public_posts(), **_f_chronological()})),
    ]

    # ================= PHOTOS =================
    photos = [
        ("Public photos", f'q="{term}", public posts', _search_url(term, "photos", _f_public_posts())),
        ("Photos tagged at a location (edit ID_PLACEHOLDER)", f'q="{term}", location={ID_PLACEHOLDER}',
         _search_url(term, "photos", _f_tagged_location(ID_PLACEHOLDER))),
    ]
    if year_from or year_to:
        y1, y2 = year_from or year_to, year_to or year_from
        photos.append((f"Public photos within {y1}-{y2}", f'q="{term}", date {y1}-{y2}',
                       _search_url(term, "photos", {**_f_public_posts(), **_f_date_range(y1, y2)})))
    sections["Photo-Dorks"] = photos

    # ================= VIDEOS =================
    sections["Video-Dorks"] = [
        ("Public videos", f'q="{term}", public posts', _search_url(term, "videos", _f_public_posts())),
        ("Live videos", f'q="{term}", source=live', _search_url(term, "videos", _f_video_source("videos_live"))),
        ("Episodes/shows", f'q="{term}", source=episodes', _search_url(term, "videos", _f_video_source("videos_episode"))),
    ]

    # ================= PAGES =================
    sections["Page-Dorks"] = [
        ("Pages search (plain)", f'q="{term}", type=pages', _search_url(term, "pages")),
        ("Verified pages only", f'q="{term}", verified', _search_url(term, "pages", _f_pages_verified())),
        ("Local business/place pages", f'q="{term}", category=local business',
         _search_url(term, "pages", _f_pages_category("Local Business or Place"))),
        ("Company/organization pages", f'q="{term}", category=company',
         _search_url(term, "pages", _f_pages_category("Company/Organization/Institution"))),
        ("Brand/product pages", f'q="{term}", category=brand',
         _search_url(term, "pages", _f_pages_category("Brand or Product"))),
    ]

    # ================= PLACES (undocumented filters - plain search only) =================
    sections["Place-Dorks"] = [
        ("Places search (plain)", f'q="{term}", type=places', _search_url(term, "places")),
    ]

    # ================= EVENTS =================
    sections["Event-Dorks"] = [
        ("Events search (plain)", f'q="{term}", type=events', _search_url(term, "events")),
    ]

    # ---- normalize + dedupe ----
    final = {}
    for category, items in sections.items():
        seen = set()
        deduped = []
        for label, raw, url in items:
            if url in seen:
                continue
            seen.add(url)
            deduped.append((label, raw, url))
        final[category] = deduped

    return final