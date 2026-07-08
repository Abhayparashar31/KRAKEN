"""
engines/yandex.py
====================
Self-contained dork generator for YANDEX.

Yandex uses its OWN operator syntax, not Google's:
  - mime:<ext>        instead of filetype:<ext>
  - title:"term"      instead of intitle:"term"
  - url:"substr"       for URL substring search (rough inurl: equivalent)
  - host:"domain"      restricts to a domain (rough site: equivalent)
  - rhost:"domain.reversed" restricts including subdomains
  - date:YYYY-MM-DD..YYYY-MM-DD  instead of after:/before:
  - & (AND), | (OR), ~ (NOT near), - (exclude), "" (exact phrase)
  - !word forces exact word form (no stemming) - useful for names/handles

Yandex has NO equivalent for: allintext, allinurl, allintitle,
inanchor, allinpostauthor, numrange, related, cache, link:.
Those categories are simply omitted here rather than faked.

See instructions.txt for the full module contract.
"""
from urllib.parse import quote

NAME = "Yandex"

FILE_GROUPS = {
    "Documents (PDF/DOC/ODT)": ["pdf", "doc", "docx", "odt"],
    "Spreadsheets": ["csv", "xls", "xlsx"],
    "Text / Logs": ["txt", "log"],
    "Data Files": ["json", "xml"],
    "Web Files": ["html", "php", "asp"],
}
IMAGE_TYPES = ["jpg", "png", "gif"]  # Yandex Images UI itype filter only supports a few
VIDEO_PLATFORMS = ["youtube.com", "tiktok.com", "facebook.com", "twitter.com", "twitch.tv", "instagram.com"]
EMAIL_VARIANTS = "(!Email|!email|!E-mail|!e-mail)"
PASSWORD_VARIANTS = "(!Password|!password|!PASSWORD)"


def _j(*parts):
    return " ".join(p for p in parts if p and str(p).strip())


def _yenc(q):
    """Yandex URLs use %2B for + etc; quote() with safe='' handles this like the sample output did."""
    return quote(q, safe="")


def _web_url(q):
    return f"https://yandex.com/search/?text={_yenc(q)}"


def _image_url(q):
    return f"https://yandex.com/images/search?from=tabbar&text={_yenc(q)}"


def _video_url(q):
    return f"https://yandex.com/video/search?from=tabbar&text={_yenc(q)}"


def generate_dorks(value, ptype, date_from=None, date_to=None):
    """
    INPUT:  value, ptype, date_from/date_to ("YYYY-MM-DD" or None)
    OUTPUT: dict[str, list[tuple[str, str, str]]]
            category -> [(label, raw_dork, full_url), ...]
    """
    term = value.replace("https://", "").replace("http://", "").strip("/") if ptype == "Website / Domain" else value
    quoted = f'"{term}"'
    is_site = ptype == "Website / Domain"

    dr = f"date:{date_from}..{date_to}" if (date_from and date_to) else \
         (f"date:{date_from}.." if date_from else (f"date:..{date_to}" if date_to else ""))

    sections = {}

    general = [
        ("Exact phrase", _j(quoted, dr)),
        ("title: - word in title", _j(f'title:({quoted})', dr)),
        ("url: - substring in URL", _j(f'url:"{term}"', dr)),
        ("!word - exact word form (no stemming)", _j(f"!{term}", dr)),
    ]
    if is_site:
        general += [
            ("host: - restrict to domain", _j(f'host:"{term}"', dr)),
            ("rhost: - domain incl. subdomains", _j(f'rhost:"{".".join(reversed(term.split(".")))}"', dr)),
            ("host: + login/admin", _j(f'host:"{term}"', 'url:"login" | url:"admin"')),
        ]
    sections["General-Dorks"] = general

    sections["Operator-Dorks"] = [
        ('"phrase" - exact phrase', _j(quoted, dr)),
        ("| (OR) - either term", _j(f'({quoted} | "{term} profile")', dr)),
        ("& (AND) - all terms required", _j(f'{quoted} & ("contact" | "about")', dr)),
        ("- (exclude) - remove noisy sites", _j(quoted, "-host:pinterest.com -host:quora.com", dr)),
        ("~~ (NOT near) - exclude nearby word", _j(f'{quoted} ~~ "spam"', dr)),
        ("() (grouping) - grouped logic", _j(f'(title:({quoted}) | text:({quoted}))', dr)),
    ]

    file_mentions = []
    for label, exts in FILE_GROUPS.items():
        for ext in exts:
            file_mentions.append((f"{label} ({ext})", _j(quoted, dr, f"mime:{ext}")))
    sections["File-Mentions"] = file_mentions

    image_dorks = [("Any image result", _j(quoted, dr))]
    for ext in IMAGE_TYPES:
        image_dorks.append((f".{ext} images", _j(quoted, dr, f"mime:{ext}")))
    sections["Image-Dorks"] = image_dorks

    video_dorks = [("Any video result", _j(quoted, dr))]
    for platform in VIDEO_PLATFORMS:
        video_dorks.append((platform, _j(f'host:"{platform}"', quoted, dr)))
    sections["Video-Audio-Dorks"] = video_dorks

    email_dorks = [("Any email mention", _j(quoted, EMAIL_VARIANTS, dr))]
    for label, exts in FILE_GROUPS.items():
        if label == "Web Files":
            continue
        for ext in exts:
            email_dorks.append((f"{label} ({ext})", _j(quoted, EMAIL_VARIANTS, dr, f"mime:{ext}")))
    sections["Email-Dorks"] = email_dorks

    password_dorks = [("Any password mention", _j(quoted, PASSWORD_VARIANTS, dr))]
    for label, exts in FILE_GROUPS.items():
        if label == "Web Files":
            continue
        for ext in exts:
            password_dorks.append((f"{label} ({ext})", _j(quoted, PASSWORD_VARIANTS, dr, f"mime:{ext}")))
    sections["Password-Dorks"] = password_dorks

    intitle_dorks = []
    for label, exts in FILE_GROUPS.items():
        for ext in exts:
            intitle_dorks.append((f"{label} ({ext})", _j(f'title:({quoted})', dr, f"mime:{ext}")))
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
