"""
engines/startpage.py
=======================
Self-contained dork generator for STARTPAGE.

Startpage is a privacy-focused proxy that largely surfaces Google's
own index, so it honors most Google-style operators: site:, intitle:,
inurl:, filetype:. It has NO dedicated image/video search endpoint
comparable to Google's tbm=isch/tbm=vid (Startpage's UI has a basic
image tab but no stable public query-string API for it), and no
public date operator, allintext/allinurl/allintitle/inanchor/
allinpostauthor/numrange/related/cache equivalents. Those are
omitted rather than faked.

See instructions.txt for the full module contract.
"""
from urllib.parse import quote_plus

NAME = "Startpage"

FILE_GROUPS = {
    "Documents (PDF/DOC/ODT)": ["pdf", "doc", "docx", "odt"],
    "Spreadsheets": ["csv", "xls", "xlsx"],
    "Text / Logs": ["txt", "log"],
    "Data Files": ["json", "xml"],
    "Web Files": ["html", "php", "asp"],
}
VIDEO_PLATFORMS = ["youtube.com", "tiktok.com", "facebook.com", "twitter.com", "twitch.tv", "instagram.com"]
EMAIL_VARIANTS = "(Email OR E-mail OR email OR e-mail)"
PASSWORD_VARIANTS = "(Password OR password OR PASSWORD)"


def _j(*parts):
    return " ".join(p for p in parts if p and str(p).strip())


def _web_url(q):
    return f"https://www.startpage.com/sp/search?query={quote_plus(q)}"


def generate_dorks(value, ptype, date_from=None, date_to=None):
    """
    INPUT:  value, ptype, date_from/date_to (ignored - no public Startpage date operator)
    OUTPUT: dict[str, list[tuple[str, str, str]]]
            category -> [(label, raw_dork, full_url), ...]
            (No dedicated Image-Dorks/Video-Audio-Dorks categories -
            Startpage has no stable public endpoint for those, so they
            are omitted rather than pointing at a plain web search
            mislabeled as image/video results.)
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
            ("site + login/admin", _j(f"site:{term}", "inurl:login OR inurl:admin OR inurl:signin")),
            ("subdomains", f"site:*.{term} -site:www.{term}"),
        ]
    sections["General-Dorks"] = general

    sections["Operator-Dorks"] = [
        ('"phrase" - exact phrase', quoted),
        ("OR - either term", f'({quoted} OR "{term} profile")'),
        ("- (exclude) - remove noisy sites", _j(quoted, "-site:pinterest.com -site:quora.com")),
        ("() (grouping) - grouped logic", f'(intitle:{quoted} OR {quoted})'),
    ]

    file_mentions = []
    for label, exts in FILE_GROUPS.items():
        for ext in exts:
            file_mentions.append((f"{label} ({ext})", _j(quoted, f"filetype:{ext}")))
    sections["File-Mentions"] = file_mentions

    video_dorks = []
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
            intitle_dorks.append((f"{label} ({ext})", _j(f"intitle:{quoted}", f"filetype:{ext}")))
    sections["Intitle-Dorks"] = intitle_dorks

    final = {}
    for category, items in sections.items():
        final[category] = [(label, dork, _web_url(dork)) for label, dork in items if dork.strip()]

    return final
