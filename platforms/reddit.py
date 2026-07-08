"""
platforms/reddit.py
======================
Self-contained dork generator for REDDIT.

Reddit dorks open DIRECTLY on reddit.com/search - never routed
through a third-party search engine. This module owns both the raw
query syntax (Reddit's own search operators/filters) and the final
browsable URL.

Reference: Reddit's documented search operators/filters -
  title:, author:, selftext:, subreddit:, url:, flair:, self:yes/no,
  nsfw:yes/no, site: (external URL match), "phrase", AND, OR, -exclude
https://support.reddithelp.com/hc/en-us/articles/19696541895316
https://medium.com/@nammooo/reddit-advance-search-operators-and-filters-310206356be1

Reddit's search UI has no since:/until: query operator - date range
is a URL param (t=hour/day/week/month/year/all), not text you type
into the query. This module maps any date range picked in the wizard
to the closest supported t= bucket rather than fabricating a fake
operator.

PARAMETER-TYPE AWARENESS:
  - "Username / Handle"   -> treated as a Reddit username. Dorks lean
                             on author: plus direct /user/<name> links.
  - "Email Address"       -> local-part before "@" extracted as a
                             PROBABLE username, used the same way,
                             every label marked "(guessed from email)".
  - "Person / Full Name"  -> no username assumption; quoted free-text
                             search instead of author:.
  - "Phone Number"        -> free-text phrase search only.
  - "Website / Domain"    -> leans on url: / site-link search instead
                             of quoted free text.
  - "Generic Keyword"     -> quoted free-text search.

See instructions.txt for the full module contract.
"""
from urllib.parse import quote_plus

DOMAIN = "reddit.com"
DISPLAY_NAME = "Reddit"

BASE_SEARCH = "https://www.reddit.com/search/"


def _j(*parts):
    return " ".join(p for p in parts if p and str(p).strip())


def _url(query, result_type="link", restrict_sr=None, subreddit=None, time_bucket=None):
    """
    result_type: 'link' (posts), 'sr' (subreddits), 'user' (users), 'comment' (comments)
    subreddit: if set, search within https://www.reddit.com/r/<sub>/search/ instead
    """
    base = f"https://www.reddit.com/r/{subreddit}/search/" if subreddit else BASE_SEARCH
    params = [f"q={quote_plus(query)}", f"type={result_type}"]
    if subreddit and restrict_sr:
        params.append("restrict_sr=1")
    if time_bucket:
        params.append(f"t={time_bucket}")
    return base + "?" + "&".join(params)


def _resolve_username(value, ptype):
    if ptype == "Username / Handle":
        return value.lstrip("u/").lstrip("@").strip(), False
    if ptype == "Email Address" and "@" in value:
        return value.split("@")[0].strip(), True
    return None, False


def _date_to_bucket(date_from, date_to):
    """Reddit only supports coarse time buckets, not exact ranges - map best-effort."""
    if not date_from and not date_to:
        return None
    return "year"  # safest broad default when any range is specified; user can refine on-site


def generate_dorks(value, ptype, date_from=None, date_to=None, extra_keywords=None):
    """
    INPUT
    -----
    value, ptype, date_from, date_to : see module docstring
    extra_keywords : list[str] | None
                      Additional free-text keywords, AND-joined onto
                      every dork generated.

    OUTPUT
    ------
    dict[str, list[tuple[str, str, str]]]
        category -> [(label, raw_dork, full_url), ...]
        Every full_url points directly at reddit.com.
    """
    extra_keywords = [k.strip() for k in (extra_keywords or []) if k.strip()]
    extra_clause = " ".join(f'"{k}"' if " " in k else k for k in extra_keywords)

    username, guessed = _resolve_username(value, ptype)
    is_website = ptype == "Website / Domain"
    domain = value.replace("https://", "").replace("http://", "").strip("/") if is_website else None
    quoted = f'"{value}"' if not is_website else None
    base_term = f'url:"{domain}"' if is_website else quoted

    time_bucket = _date_to_bucket(date_from, date_to)

    sections = {}

    # ================= PEOPLE DORKS =================
    people = []
    if username:
        note = " (guessed from email)" if guessed else ""
        people += [
            (f"Posts by u/{username}{note}", _j(f"author:{username}", extra_clause),
             None),  # handled below with special user link
            (f"Direct profile link u/{username}{note}", f"u/{username}", None),
            (f"Submitted posts by u/{username}{note}", f"u/{username}/submitted", None),
            (f"Comments by u/{username}{note}", f"u/{username}/comments", None),
            (f"Posts by u/{username} matching term{note}", _j(f"author:{username}", base_term, extra_clause), None),
        ]
    elif ptype in ("Person / Full Name", "Generic Keyword"):
        people.append((f"Search for user profiles named {value}", value, None))
    sections["People-Dorks"] = people

    # ================= POST DORKS =================
    posts = [
        ("Exact phrase in posts", _j(base_term, extra_clause), "link"),
        ("Term in post title only", _j(f"title:{base_term}", extra_clause), "link"),
        ("Term in self-text (post body) only", _j(f"selftext:{base_term}", extra_clause), "link"),
        ("Self posts only (text posts)", _j(base_term, "self:yes", extra_clause), "link"),
        ("Link posts only (excludes text posts)", _j(base_term, "self:no", extra_clause), "link"),
    ]
    sections["Post-Dorks"] = posts

    # ================= SUBREDDIT DORKS =================
    subreddit_dorks = [
        ("Matching subreddit names", base_term, "sr"),
        (f"Search within a specific subreddit (edit SUBREDDIT)",
         _j(base_term, extra_clause), "link_in_sub"),
    ]
    sections["Subreddit-Dorks"] = subreddit_dorks

    # ================= URL DORKS =================
    if is_website:
        url_dorks = [
            ("Posts linking to this domain", _j(f'url:"{domain}"', extra_clause), "link"),
            ("Posts linking to this domain, self posts excluded", _j(f'url:"{domain}"', "self:no", extra_clause), "link"),
        ]
    else:
        url_dorks = [("Posts containing this term with any external link", _j(base_term, "self:no", extra_clause), "link")]
    sections["URL-Dorks"] = url_dorks

    # ================= FLAIR / NSFW DORKS =================
    sections["Flair-NSFW-Dorks"] = [
        ("Matching a specific flair (edit FLAIR_TEXT)", _j(base_term, 'flair:"FLAIR_TEXT"', extra_clause), "link"),
        ("Excluding NSFW-flagged posts", _j(base_term, "nsfw:no", extra_clause), "link"),
        ("Only NSFW-flagged posts", _j(base_term, "nsfw:yes", extra_clause), "link"),
    ]

    # ================= COMMENT DORKS =================
    sections["Comment-Dorks"] = [
        ("Term mentioned in comments", _j(base_term, extra_clause), "comment"),
    ]
    if username:
        sections["Comment-Dorks"].append(
            (f"Comments by u/{username} mentioning term", _j(f"author:{username}", base_term, extra_clause), "comment")
        )

    # ================= DATE / TIME DORKS =================
    date_dorks = []
    if time_bucket:
        date_dorks.append((f"Within approx. selected range (t={time_bucket})", _j(base_term, extra_clause), ("link", time_bucket)))
    date_dorks += [
        ("Past 24 hours", _j(base_term, extra_clause), ("link", "day")),
        ("Past week", _j(base_term, extra_clause), ("link", "week")),
        ("Past month", _j(base_term, extra_clause), ("link", "month")),
        ("Past year", _j(base_term, extra_clause), ("link", "year")),
        ("All time", _j(base_term, extra_clause), ("link", "all")),
    ]
    sections["Date-Time-Dorks"] = date_dorks

    # ================= ADVANCED OPERATORS =================
    first_kw = value.split()[0] if value.split() else value
    sections["Operator-Dorks"] = [
        ('"phrase" - exact phrase', _j(base_term, extra_clause), "link"),
        ("OR - either term", _j(f'({base_term} OR "{value} update")', extra_clause), "link"),
        ("AND - all terms required", _j(f'{base_term} AND ("contact" OR "about")', extra_clause), "link"),
        ("- (exclude) - remove a term", _j(base_term, f"-{first_kw}spam", extra_clause), "link"),
        ("() (grouping) - combined logic", _j(f'({base_term}) self:no -flair:"meme"', extra_clause), "link"),
    ]

    # ---- normalize everything into (label, raw_dork, url) ----
    final = {}
    for category, items in sections.items():
        seen = set()
        deduped = []
        for entry in items:
            label, raw = entry[0], entry[1]
            extra = entry[2] if len(entry) > 2 else "link"
            raw = " ".join(raw.split()) if raw else raw

            if raw in (None,):
                continue
            if raw in seen:
                continue
            seen.add(raw)

            # Special-case direct profile/user links (no query, just a path)
            if raw.startswith("u/"):
                url = f"https://www.reddit.com/{raw}/"
            elif extra == "sr":
                url = _url(raw, result_type="sr")
            elif extra == "link_in_sub":
                url = _url(raw, result_type="link", subreddit="SUBREDDIT", restrict_sr=True)
            elif isinstance(extra, tuple):
                rtype, bucket = extra
                url = _url(raw, result_type=rtype, time_bucket=bucket)
            elif extra == "comment":
                url = _url(raw, result_type="comment")
            else:
                url = _url(raw, result_type="link")

            deduped.append((label, raw, url))
        final[category] = deduped

    return final