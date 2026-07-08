"""
engines/duckduckgo.py
=======================
Self-contained dork generator for DUCKDUCKGO.

DuckDuckGo shares most Google-style bang operators (site:, filetype:,
intitle:, inurl:) but does NOT support after:/before: date filtering
or several advanced operators (allintext, allinurl, inanchor,
allinpostauthor, numrange, related, cache, link). Those are omitted
here rather than faked - DDG search does not honor them and Kraken
should not generate dorks that silently do nothing.

See instructions.txt for the full module contract.
"""
from urllib.parse import quote_plus

NAME = "DuckDuckGo"

FILE_GROUPS = {
    "Documents (PDF/DOC/ODT)": ["pdf", "doc", "docx", "odt"],
    "Spreadsheets": ["csv", "xls", "xlsx"],
    "Text / Logs": ["txt", "log"],
    "Data Files": ["json", "xml"],
    "Web Files": ["html", "php", "asp"],
}
IMAGE_TYPES = ["png", "jpg", "jpeg", "gif", "ico", "bmp", "svg", "webp"]
VIDEO_PLATFORMS = ["youtube.com", "tiktok.com", "facebook.com", "twitter.com", "twitch.tv", "instagram.com"]
EMAIL_VARIANTS = "(Email OR E-mail OR email OR e-mail)"
PASSWORD_VARIANTS = "(Password OR password OR PASSWORD)"


def _j(*parts):
    return " ".join(p for p in parts if p and str(p).strip())


def _web_url(q):
    return f"https://duckduckgo.com/?q={quote_plus(q)}"


def _image_url(q):
    return f"https://duckduckgo.com/?q={quote_plus(q)}&iax=images&ia=images"


def _video_url(q):
    return f"https://duckduckgo.com/?q={quote_plus(q)}&iax=videos&ia=videos"


def generate_dorks(value, ptype, date_from=None, date_to=None):
    """
    INPUT:  value, ptype, date_from/date_to (ignored - DDG has no date operator)
    OUTPUT: dict[str, list[tuple[str, str, str]]]
            category -> [(label, raw_dork, full_url), ...]
    """
    term = value.replace("https://", "").replace("http://", "").strip("/") if ptype == "Website / Domain" else value
    quoted = f'"{term}"'
    is_site = ptype == "Website / Domain"

    sections = {}

    general = [
        ("Exact phrase", quoted),
        ("intext - word anywhere in text", f"intext:({quoted})"),
        ("inurl - word in URL", f"inurl:({quoted})"),
        ("intitle - word in title", f"intitle:({quoted})"),
    ]
    if is_site:
        general += [
            ("site - restrict to domain", f"site:{term}"),
            ("site + login/admin", _j(f"site:{term}", "inurl:login OR inurl:admin OR inurl:signin")),
            ("subdomains", f"site:*.{term} -site:www.{term}"),
        ]
    sections["General-Dorks"] = general

    first_word = term.split()[0] if term.split() else term
    sections["Operator-Dorks"] = [
        ('"phrase" - exact phrase', quoted),
        ("OR - either term", f'({quoted} OR "{term} profile")'),
        ("- (exclude) - remove noisy sites", _j(quoted, "-site:pinterest.com -site:quora.com")),
        ("+ (force include) - pin a term", _j(quoted, f"+{first_word}")),
        ("* (wildcard) - unknown word/pattern", f'"{term} *"'),
        ("() (grouping) - grouped logic", f'(intitle:({quoted}) OR intext:({quoted}))'),
    ]

    file_mentions = []
    for label, exts in FILE_GROUPS.items():
        for ext in exts:
            file_mentions.append((f"{label} ({ext})", _j(f"intext:({quoted})", f"filetype:{ext}")))
    sections["File-Mentions"] = file_mentions

    image_dorks = [("Any image result", quoted)]
    for ext in IMAGE_TYPES:
        image_dorks.append((f".{ext} images", _j(quoted, f"filetype:{ext}")))
    sections["Image-Dorks"] = image_dorks

    video_dorks = [("Any video result", quoted)]
    for platform in VIDEO_PLATFORMS:
        video_dorks.append((platform, _j(f"site:{platform}", quoted)))
    sections["Video-Audio-Dorks"] = video_dorks

    email_dorks = [("Any email mention", _j(quoted, EMAIL_VARIANTS))]
    for label, exts in FILE_GROUPS.items():
        if label == "Web Files":
            continue
        for ext in exts:
            email_dorks.append((f"{label} ({ext})", _j(quoted, EMAIL_VARIANTS, f"filetype:{ext}")))
    sections["Email-Dorks"] = email_dorks

    password_dorks = [("Any password mention", _j(quoted, PASSWORD_VARIANTS))]
    for label, exts in FILE_GROUPS.items():
        if label == "Web Files":
            continue
        for ext in exts:
            password_dorks.append((f"{label} ({ext})", _j(quoted, PASSWORD_VARIANTS, f"filetype:{ext}")))
    sections["Password-Dorks"] = password_dorks

    intitle_dorks = []
    for label, exts in FILE_GROUPS.items():
        for ext in exts:
            intitle_dorks.append((label, _j(f"intitle:({quoted})", f"filetype:{ext}")))
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
