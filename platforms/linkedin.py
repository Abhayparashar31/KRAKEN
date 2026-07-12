"""
platforms/linkedin.py
========================
Self-contained dork generator for LINKEDIN - native search edition.

LinkedIn has a real, documented search syntax (unlike Instagram) but
with one major caveat that applies to EVERY dork in this module:
LinkedIn requires an active logged-in session for search to return
anything. Logged-out visitors are redirected to a login wall almost
immediately - this is stricter than Facebook (which shows partial
public results logged out) and worth knowing before relying on these
links in an incognito/logged-out browser.

Reference (LinkedIn's own Help Center, publicly documented):
  https://www.linkedin.com/help/linkedin/answer/a524335  (Boolean search)
  https://www.linkedin.com/help/linkedin/answer/a525054  (People search)
  https://www.linkedin.com/help/linkedin/answer/a1340735 (Company page URLs)

Native URL patterns used here:
    https://www.linkedin.com/in/<vanity-name>/                    (profile)
    https://www.linkedin.com/company/<company-slug>/               (company page)
    https://www.linkedin.com/search/results/people/?keywords=...   (people search)
    https://www.linkedin.com/search/results/companies/?keywords=...(company search)
    https://www.linkedin.com/search/results/content/?keywords=...  (posts search)
    https://www.linkedin.com/jobs/search/?keywords=...              (jobs search)

Boolean search rules LinkedIn documents (applied to the query text,
not URL structure): AND / OR / NOT must be UPPERCASE, "quotes" for
exact phrases, ( ) for grouping. LinkedIn does NOT support +, -,
wildcards (*), or brackets/braces - those are silently ignored or
break the query, so this module never generates them.

PARAMETER-TYPE AWARENESS:
  - "Username / Handle"   -> treated as a LinkedIn vanity URL slug
                             (linkedin.com/in/<slug>).
  - "Email Address"       -> local-part before "@" extracted as a
                             PROBABLE vanity slug, labeled as a guess
                             (LinkedIn slugs rarely match email
                             local-parts exactly, so this is a weaker
                             guess than on other platforms - flagged
                             accordingly).
  - "Person / Full Name"  -> no slug assumption; Boolean keyword
                             search instead.
  - "Phone Number"        -> not meaningful on LinkedIn profiles;
                             falls back to a plain keyword search.
  - "Website / Domain"    -> used to search company pages/posts that
                             might reference that domain.
  - "Generic Keyword"     -> plain Boolean keyword search.

See instructions.txt for the full module contract.
"""
from urllib.parse import quote_plus

DOMAIN = "linkedin.com"
DISPLAY_NAME = "LinkedIn"


def _people_url(keywords):
    return f"https://www.linkedin.com/search/results/people/?keywords={quote_plus(keywords)}"


def _company_search_url(keywords):
    return f"https://www.linkedin.com/search/results/companies/?keywords={quote_plus(keywords)}"


def _content_url(keywords):
    return f"https://www.linkedin.com/search/results/content/?keywords={quote_plus(keywords)}"


def _jobs_url(keywords):
    return f"https://www.linkedin.com/jobs/search/?keywords={quote_plus(keywords)}"


def _profile_url(slug):
    return f"https://www.linkedin.com/in/{slug}/"


def _company_page_url(slug):
    return f"https://www.linkedin.com/company/{slug}/"


def _resolve_slug(value, ptype):
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
    date_from, date_to : accepted for contract consistency but UNUSED -
                          LinkedIn's public search has no date-range
                          keyword operator.
    extra_keywords : list[str] | None
                      Combined with AND (LinkedIn's real Boolean
                      operator, must stay uppercase) onto the main
                      search term.

    OUTPUT
    ------
    dict[str, list[tuple[str, str, str]]]
        category -> [(label, raw_dork, native_url), ...]
        Every native_url is a real linkedin.com URL. Login is
        required for results to actually appear - see module
        docstring.
    """
    extra_keywords = [k.strip() for k in (extra_keywords or []) if k.strip()]
    extra_clause = " AND ".join(f'"{k}"' if " " in k else k for k in extra_keywords)

    slug, guessed = _resolve_slug(value, ptype)
    is_website = ptype == "Website / Domain"
    domain = value.replace("https://", "").replace("http://", "").strip("/") if is_website else None
    quoted = f'"{value}"' if not is_website else f'"{domain}"'

    def with_extra(base):
        return f"{base} AND {extra_clause}" if extra_clause else base

    sections = {}

    # ================= PEOPLE =================
    people = []
    if slug:
        note = " (guessed from email - LinkedIn slugs rarely match exactly)" if guessed else ""
        people.append((f"Direct profile{note}", f"linkedin.com/in/{slug}/", _profile_url(slug)))
    people.append(("People search (Boolean keyword)", f'keywords={with_extra(quoted)}',
                   _people_url(with_extra(quoted))))
    if not is_website and " " in value:
        first, *rest = value.split(" ")
        people.append(("People search, name split AND-combined", f'keywords={first} AND {" ".join(rest)}',
                       _people_url(f"{first} AND {' '.join(rest)}")))
    sections["People-Dorks"] = people

    # ================= COMPANIES =================
    company = [
        ("Company search (Boolean keyword)", f'keywords={with_extra(quoted)}', _company_search_url(with_extra(quoted))),
    ]
    if is_website:
        company.append((f"Direct company page (edit slug if known)", f"linkedin.com/company/{domain.split('.')[0]}/",
                        _company_page_url(domain.split(".")[0])))
    sections["Company-Dorks"] = company

    # ================= POSTS / CONTENT =================
    sections["Post-Dorks"] = [
        ("Posts mentioning term (Boolean keyword)", f'keywords={with_extra(quoted)}', _content_url(with_extra(quoted))),
        ("Posts, exact phrase only", f'keywords={quoted}', _content_url(quoted)),
    ]

    # ================= JOBS =================
    sections["Job-Dorks"] = [
        ("Job postings mentioning term", f'keywords={with_extra(quoted)}', _jobs_url(with_extra(quoted))),
    ]
    if slug:
        sections["Job-Dorks"].append(
            (f"Jobs posted referencing @{slug}", f'keywords={slug}', _jobs_url(slug))
        )

    # ================= BOOLEAN OPERATOR EXAMPLES =================
    first_kw = value.split()[0] if value.split() else value
    sections["Operator-Dorks"] = [
        ('"phrase" - exact phrase', quoted, _people_url(quoted)),
        ("AND - all terms required (must be UPPERCASE)", f'{quoted} AND "hiring"', _people_url(f'{quoted} AND "hiring"')),
        ("OR - either term (must be UPPERCASE)", f'{quoted} OR "{first_kw} official"', _people_url(f'{quoted} OR "{first_kw} official"')),
        ("NOT - exclude a term (must be UPPERCASE)", f'{quoted} NOT "recruiter"', _people_url(f'{quoted} NOT "recruiter"')),
        ("() - grouped logic", f'{quoted} AND ("engineer" OR "developer")', _people_url(f'{quoted} AND ("engineer" OR "developer")')),
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