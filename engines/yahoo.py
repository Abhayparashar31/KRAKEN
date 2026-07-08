"""
engines/yahoo.py
===================
Self-contained dork generator for YAHOO.

Yahoo Search still honors a small, Google-like operator subset:
  site:, intitle:, inurl:, link:, "phrase", -exclude, OR
Yahoo does NOT reliably honor: filetype:, allintext, allinurl,
allintitle, inanchor, allinpostauthor, numrange, related:, cache:,
or date filtering via any public operator. Those categories are
omitted rather than faked. (Yahoo Search results are also partly
powered by Bing under the hood, so operator support can shift.)

See instructions.txt for the full module contract.
"""
from urllib.parse import quote_plus

NAME = "Yahoo"

VIDEO_PLATFORMS = ["youtube.com", "tiktok.com", "facebook.com", "twitter.com", "twitch.tv", "instagram.com"]
EMAIL_VARIANTS = "(Email OR E-mail OR email OR e-mail)"
PASSWORD_VARIANTS = "(Password OR password OR PASSWORD)"


def _j(*parts):
    return " ".join(p for p in parts if p and str(p).strip())


def _web_url(q):
    return f"https://search.yahoo.com/search?p={quote_plus(q)}"


def _image_url(q):
    return f"https://images.search.yahoo.com/search/images?p={quote_plus(q)}"


def _video_url(q):
    return f"https://video.search.yahoo.com/search/video?p={quote_plus(q)}"


def generate_dorks(value, ptype, date_from=None, date_to=None):
    """
    INPUT:  value, ptype, date_from/date_to (ignored - no public Yahoo date operator)
    OUTPUT: dict[str, list[tuple[str, str, str]]]
            category -> [(label, raw_dork, full_url), ...]
    """
    term = value.replace("https://", "").replace("http://", "").strip("/") if ptype == "Website / Domain" else value
    quoted = f'"{term}"'
    is_site = ptype == "Website / Domain"

    sections = {}

    general = [
        ("Exact phrase", quoted),
        ("intitle - word in title", f"intitle:{quoted}"),
        ("inurl - word in URL", f"inurl:{term.replace(' ', '-')}"),
    ]
    if is_site:
        general += [
            ("site - restrict to domain", f"site:{term}"),
            ("link - pages linking to this site", f"link:{term}"),
            ("site + login/admin", _j(f"site:{term}", "inurl:login OR inurl:admin")),
        ]
    else:
        general.append(("link - pages linking to a related profile", f'link:"{term}"'))
    sections["General-Dorks"] = general

    sections["Operator-Dorks"] = [
        ('"phrase" - exact phrase', quoted),
        ("OR - either term", f'({quoted} OR "{term} profile")'),
        ("- (exclude) - remove noisy sites", _j(quoted, "-site:pinterest.com -site:quora.com")),
        ("() (grouping) - grouped logic", f'(intitle:{quoted} OR {quoted})'),
    ]

    # Yahoo's filetype: support is unreliable, but many results still surface
    # when combined with intext-style phrase + extension hint, so keep a
    # best-effort File-Mentions section rather than omitting it entirely.
    file_groups = {
        "Documents (PDF/DOC/ODT)": ["pdf", "doc", "docx", "odt"],
        "Spreadsheets": ["csv", "xls", "xlsx"],
        "Text / Logs": ["txt", "log"],
    }
    file_mentions = []
    for label, exts in file_groups.items():
        for ext in exts:
            file_mentions.append((f"{label} ({ext})", _j(quoted, f"filetype:{ext}")))
    sections["File-Mentions"] = file_mentions

    sections["Image-Dorks"] = [("Any image result", quoted)]

    video_dorks = [("Any video result", quoted)]
    for platform in VIDEO_PLATFORMS:
        video_dorks.append((platform, _j(f"site:{platform}", quoted)))
    sections["Video-Audio-Dorks"] = video_dorks

    email_dorks = [("Any email mention", _j(quoted, EMAIL_VARIANTS))]
    for label, exts in file_groups.items():
        for ext in exts:
            email_dorks.append((f"{label} ({ext})", _j(quoted, EMAIL_VARIANTS, f"filetype:{ext}")))
    sections["Email-Dorks"] = email_dorks

    password_dorks = [("Any password mention", _j(quoted, PASSWORD_VARIANTS))]
    for label, exts in file_groups.items():
        for ext in exts:
            password_dorks.append((f"{label} ({ext})", _j(quoted, PASSWORD_VARIANTS, f"filetype:{ext}")))
    sections["Password-Dorks"] = password_dorks

    intitle_dorks = []
    for label, exts in file_groups.items():
        for ext in exts:
            intitle_dorks.append((f"{label} ({ext})", _j(f"intitle:{quoted}", f"filetype:{ext}")))
    sections["Intitle-Dorks"] = intitle_dorks

    final = {}
    for category, items in sections.items():
        if category == "Image-Dorks":
            url_fn = _image_url
        elif category == "Video-Audio-Dorks":
            url_fn = _video_url
        else:
            url_fn = _web_url
        final[category] = [(label, dork, url_fn(dork)) for label, dork in items if dork.strip()]

    return final
