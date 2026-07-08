"""
engines/google.py
===================
Self-contained dork generator for GOOGLE.

Every engine module owns its FULL pipeline: it knows Google's specific
operator syntax (after:/before:, filetype:, tbm=isch, etc.) and builds
both the raw dork string AND the final clickable URL itself. app.py
does not know anything about Google-specific syntax - it just calls
generate_dorks() and displays what comes back.

See instructions.txt for the full module contract every engine file
(google.py, yandex.py, bing.py, ...) must follow.
"""
from urllib.parse import quote_plus

NAME = "Google"

FILE_GROUPS = {
    "Documents (PDF/DOC/ODT)": ["pdf", "doc", "docx", "odt"],
    "Spreadsheets": ["csv", "xls", "xlsx"],
    "Text / Logs": ["txt", "log"],
    "Data Files": ["json", "xml"],
    "Web Files": ["html", "php", "asp"],
}
IMAGE_TYPES = ["png", "jpg", "jpeg", "gif", "raw", "ico", "bmp", "svg", "webp"]
VIDEO_PLATFORMS = ["youtube.com", "tiktok.com", "facebook.com", "twitter.com", "twitch.tv", "instagram.com"]
EMAIL_VARIANTS = "(Email OR E-mail OR email OR e-mail)"
PASSWORD_VARIANTS = "(Password OR password OR PASSWORD)"


def _j(*parts):
    return " ".join(p for p in parts if p and str(p).strip())


def _web_url(q):
    return f"https://www.google.com/search?q={quote_plus(q)}"


def _image_url(q):
    return f"https://www.google.com/search?q={quote_plus(q)}&hl=&tbm=isch&source=hp&biw=&bih=&sclient=img"


def _video_url(q):
    return f"https://www.google.com/search?q={quote_plus(q)}&hl=&tbm=vid&ei=&sclient=gws-wiz-video"


def generate_dorks(value, ptype, date_from=None, date_to=None):
    """
    INPUT:  value, ptype, date_from ("YYYY-MM-DD" or None), date_to
    OUTPUT: dict[str, list[tuple[str, str, str]]]
            category -> [(label, raw_dork, full_url), ...]
    """
    term = value.replace("https://", "").replace("http://", "").strip("/") if ptype == "Website / Domain" else value
    quoted = f'"{term}"'
    is_site = ptype == "Website / Domain"

    dr = ""
    if date_from:
        dr = _j(dr, f"after:{date_from}")
    if date_to:
        dr = _j(dr, f"before:{date_to}")

    sections = {}

    general = [
        ("Exact phrase", _j(quoted, dr)),
        ("allintext - all words in body", _j(f"allintext: {term}", dr)),
        ("intext - word anywhere in text", _j(f"intext:({quoted})", dr)),
        ("inurl - word in URL", _j(f"inurl:({quoted})", dr)),
        ("allinurl - all words in URL", _j(f"allinurl: {term}", dr)),
        ("intitle - word in title", _j(f"intitle:({quoted})", dr)),
        ("allintitle - all words in title", _j(f"allintitle: {term}", dr)),
        ("inanchor - inbound link anchor text", _j(f"inanchor:({quoted})", dr)),
        ("allinpostauthor - blog posts by author", _j(f"allinpostauthor:{term}", dr)),
    ]
    if is_site:
        general += [
            ("site - restrict to domain", _j(f"site:{term}", dr)),
            ("link - pages linking to this site", f"link:{term}"),
            ("related - similar sites", f"related:{term}"),
            ("cache - Google's cached copy", f"cache:{term}"),
            ("site + login/admin", _j(f"site:{term}", "inurl:login OR inurl:admin OR inurl:signin")),
            ("site + exposed config/backup", _j(f"site:{term}", "(inurl:config OR inurl:backup OR inurl:.env OR inurl:.git)")),
            ("subdomains", f"site:*.{term} -site:www.{term}"),
        ]
    else:
        general += [
            ("link - pages linking to a related profile", f'link:"{term}"'),
            ("numrange - numeric range near term", _j(quoted, "1000..9999", dr)),
        ]
    sections["General-Dorks"] = general

    first_word = term.split()[0] if term.split() else term
    sections["Operator-Dorks"] = [
        ('"phrase" - exact phrase', _j(quoted, dr)),
        ("OR - either term", _j(f'({quoted} OR "{term} profile")', dr)),
        ("AND - all terms required", _j(f'{quoted} AND ("contact" OR "about")', dr)),
        ("- (exclude) - remove noisy sites", _j(quoted, "-site:pinterest.com -site:quora.com", dr)),
        ("+ (force include) - pin a term", _j(quoted, f"+{first_word}", dr)),
        ("~ (synonym) - include related words", _j(f"~{term}", dr)),
        ("* (wildcard) - unknown word/pattern", _j(f'"{term} *"', dr)),
        ("() (grouping) - grouped logic", _j(f'(intitle:({quoted}) OR intext:({quoted}))', dr)),
        ("Combined AND + OR + exclusion", _j(f'{quoted} AND (profile OR bio) -inurl:login', dr)),
    ]

    file_mentions = []
    for label, exts in FILE_GROUPS.items():
        for ext in exts:
            file_mentions.append((f"{label} ({ext})", _j(f"intext:({quoted})", dr, f"filetype:{ext}")))
    sections["File-Mentions"] = file_mentions

    image_dorks = [("Any image result", _j(quoted, dr))]
    for ext in IMAGE_TYPES:
        image_dorks.append((f".{ext} images", _j(quoted, dr, f"filetype:{ext}")))
    sections["Image-Dorks"] = image_dorks

    video_dorks = [("Any video result", _j(quoted, dr))]
    for platform in VIDEO_PLATFORMS:
        video_dorks.append((platform, _j(f"site:{platform}", quoted, dr)))
    sections["Video-Audio-Dorks"] = video_dorks

    email_dorks = [("Any email mention", _j(quoted, EMAIL_VARIANTS, dr))]
    for label, exts in FILE_GROUPS.items():
        if label == "Web Files":
            continue
        for ext in exts:
            email_dorks.append((f"{label} ({ext})", _j(quoted, EMAIL_VARIANTS, dr, f"filetype:{ext}")))
    sections["Email-Dorks"] = email_dorks

    password_dorks = [("Any password mention", _j(quoted, PASSWORD_VARIANTS, dr))]
    for label, exts in FILE_GROUPS.items():
        if label == "Web Files":
            continue
        for ext in exts:
            password_dorks.append((f"{label} ({ext})", _j(quoted, PASSWORD_VARIANTS, dr, f"filetype:{ext}")))
    sections["Password-Dorks"] = password_dorks

    intitle_dorks = []
    for label, exts in FILE_GROUPS.items():
        for ext in exts:
            intitle_dorks.append((label, _j(f"intitle:({quoted})", dr, f"filetype:{ext}")))
    sections["Intitle-Dorks"] = intitle_dorks

    # attach URLs -> convert every (label, dork) into (label, dork, url)
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
