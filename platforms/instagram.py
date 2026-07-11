"""
platforms/instagram.py
=========================
Self-contained dork generator for INSTAGRAM - NATIVE-ONLY EDITION.

Every dork in this module opens directly on instagram.com. There are
NO site:/inurl:/filetype: operator-based dorks here and nothing is
routed through a search engine - by explicit design choice.

This means the dork count is small and category-limited, because
Instagram genuinely only exposes a handful of stable, public,
directly-clickable URL patterns without requiring a logged-in
session:
    https://www.instagram.com/<username>/               (profile / posts grid)
    https://www.instagram.com/<username>/reels/           (reels tab)
    https://www.instagram.com/<username>/tagged/           (tagged-in posts tab)
    https://www.instagram.com/explore/tags/<tag>/          (hashtag page)
    https://www.instagram.com/explore/locations/<id>/      (place page -
        requires a numeric location ID, since Instagram doesn't accept
        a location name directly in the URL)

There is NO native way to search Instagram by a person's name or
free-text keyword without either being logged in (Instagram's own
keyword-search endpoint is session-gated) or falling back to a search
engine (which this module intentionally does not do). If the
parameter type isn't a username/handle, the People-Dorks category
will be empty rather than silently substituting a browser-routed
dork - see the "no dorks available" note generated in that case.

PARAMETER-TYPE AWARENESS:
  - "Username / Handle"   -> the only case with rich results: profile,
                             reels tab, tagged tab.
  - "Email Address"       -> local-part before "@" extracted as a
                             PROBABLE username, labeled as a guess,
                             used the same way as an explicit handle.
  - "Person / Full Name"  -> no native people-search exists; only a
                             hashtag-style dork is generated (treating
                             the name as a possible hashtag).
  - "Phone Number"        -> no native dork possible at all (nothing
                             to build a profile/tag/location URL from).
  - "Website / Domain"    -> no native dork possible.
  - "Generic Keyword"     -> hashtag-style dork only.

See instructions.txt for the full module contract.
"""

DOMAIN = "instagram.com"
DISPLAY_NAME = "Instagram"

LOCATION_ID_PLACEHOLDER = "LOCATION_ID"


def _profile_url(username):
    return f"https://www.instagram.com/{username}/"


def _reels_url(username):
    return f"https://www.instagram.com/{username}/reels/"


def _tagged_url(username):
    return f"https://www.instagram.com/{username}/tagged/"


def _tag_url(tag):
    return f"https://www.instagram.com/explore/tags/{tag}/"


def _location_url(location_id):
    return f"https://www.instagram.com/explore/locations/{location_id}/"


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
    value, ptype : see module docstring
    date_from, date_to, extra_keywords : accepted for contract
        consistency with other platform modules but UNUSED - Instagram's
        native URLs have no date-filter or keyword-stacking mechanism.

    OUTPUT
    ------
    dict[str, list[tuple[str, str, str]]]
        category -> [(label, raw_dork, native_url), ...]
        every native_url is a real, directly-clickable instagram.com
        link - no entry in this module ever has url=None and nothing
        is ever routed through a search engine.
    """
    username, guessed = _resolve_username(value, ptype)
    note = " (guessed from email)" if guessed else ""

    sections = {}

    # ================= PEOPLE (only populated when a username is known) =================
    people = []
    if username:
        people = [
            (f"Profile / posts grid{note}", f"instagram.com/{username}/", _profile_url(username)),
            (f"Reels tab{note}", f"instagram.com/{username}/reels/", _reels_url(username)),
            (f"Tagged-in posts tab{note}", f"instagram.com/{username}/tagged/", _tagged_url(username)),
        ]
    sections["People-Dorks"] = people

    # ================= TAGS (works for any value, treated as a hashtag) =================
    tag_term = value.replace(" ", "") if value else value
    sections["Tag-Dorks"] = [
        (f"Hashtag page #{tag_term}", f"#{tag_term}", _tag_url(tag_term)),
    ]

    # ================= PLACES (needs a numeric location ID) =================
    sections["Place-Dorks"] = [
        (f"Location page (edit {LOCATION_ID_PLACEHOLDER})",
         f"instagram.com/explore/locations/{LOCATION_ID_PLACEHOLDER}/",
         _location_url(LOCATION_ID_PLACEHOLDER)),
    ]

    return sections