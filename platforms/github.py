"""
platforms/github.py
======================
Self-contained dork generator for GITHUB - native search edition.

GitHub has a genuinely public, well-documented search system (unlike
Facebook's reverse-engineered filters or Instagram's near-total lack
of one). Reference:
  https://docs.github.com/en/search-github/searching-on-github
Every dork below uses real, currently-supported GitHub search
qualifiers and opens directly on github.com - no operator-through-a-
search-engine fallback needed here, since GitHub's own search covers
everything this module needs.

SCOPE - deliberately excluded:
This module does NOT generate "GitHub dorking for exposed secrets"
queries (filename:.env, extension:pem, "BEGIN RSA PRIVATE KEY",
api_key/password hunting, etc.). That's a recognized technique for
finding accidentally-leaked credentials with the implication of using
them to access systems you don't own - a meaningfully different thing
from discovering someone's public profile, repos, or contribution
history. Everything in this module surfaces intentionally public
activity (profiles, repos, code, issues, commits) rather than
accidental exposure.

PARAMETER-TYPE AWARENESS:
  - "Username / Handle"   -> treated as a GitHub username. Enables
                             direct profile/repos/stars/gists links
                             plus author:-scoped search.
  - "Email Address"       -> local-part before "@" extracted as a
                             PROBABLE username, labeled as a guess
                             (GitHub also lets you search commits by
                             committer email directly - included).
  - "Person / Full Name"  -> no username assumption; quoted free-text
                             user search instead (GitHub user search
                             does match display names, not just
                             usernames).
  - "Phone Number"        -> not meaningful on GitHub; falls back to
                             a plain quoted code/repo search.
  - "Website / Domain"    -> used to search for repos/code referencing
                             that domain (e.g. finding projects that
                             link to a company site).
  - "Generic Keyword"     -> quoted free-text search across repos/code.

See instructions.txt for the full module contract.
"""
from urllib.parse import quote_plus

DOMAIN = "github.com"
DISPLAY_NAME = "GitHub"


def _j(*parts):
    return " ".join(p for p in parts if p and str(p).strip())


def _search_url(query, search_type="repositories"):
    return f"https://github.com/search?q={quote_plus(query)}&type={search_type}"


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
    value, ptype, date_from, date_to : see module docstring.
                                        date_from/date_to (ISO dates)
                                        map to GitHub's created:/
                                        pushed: range qualifiers.
    extra_keywords : list[str] | None
                      AND-joined onto every search-query dork.

    OUTPUT
    ------
    dict[str, list[tuple[str, str, str]]]
        category -> [(label, raw_dork, native_url), ...]
        Every native_url is a real, directly-clickable github.com URL.
    """
    extra_keywords = [k.strip() for k in (extra_keywords or []) if k.strip()]
    extra_clause = " ".join(f'"{k}"' if " " in k else k for k in extra_keywords)

    username, guessed = _resolve_username(value, ptype)
    is_website = ptype == "Website / Domain"
    domain = value.replace("https://", "").replace("http://", "").strip("/") if is_website else None
    quoted = f'"{value}"' if not is_website else f'"{domain}"'

    date_range = ""
    if date_from and date_to:
        date_range = f"{date_from}..{date_to}"
    elif date_from:
        date_range = f">={date_from}"
    elif date_to:
        date_range = f"<={date_to}"

    sections = {}

    # ================= PEOPLE =================
    people = []
    if username:
        note = " (guessed from email)" if guessed else ""
        people += [
            (f"Profile{note}", f"github.com/{username}", f"https://github.com/{username}"),
            (f"Repositories{note}", f"github.com/{username}?tab=repositories", f"https://github.com/{username}?tab=repositories"),
            (f"Starred repos{note}", f"github.com/{username}?tab=stars", f"https://github.com/{username}?tab=stars"),
            (f"Followers{note}", f"github.com/{username}?tab=followers", f"https://github.com/{username}?tab=followers"),
            (f"Following{note}", f"github.com/{username}?tab=following", f"https://github.com/{username}?tab=following"),
            (f"Gists{note}", f"gist.github.com/{username}", f"https://gist.github.com/{username}"),
        ]
    else:
        people.append(("User search by display name", f'q={value}, type=users', _search_url(value, "users")))
    sections["People-Dorks"] = people

    # ================= REPOSITORIES =================
    repo_dorks = [
        ("Repositories matching term", f'q="{value}", type=repositories', _search_url(_j(quoted, extra_clause), "repositories")),
    ]
    if username:
        repo_dorks.append((f"Repositories owned by @{username}", f'user:{username}',
                           _search_url(f"user:{username}", "repositories")))

    if date_range:
        repo_dorks.append((f"Repositories created in range", f'q="{value}" created:{date_range}',
                           _search_url(_j(quoted, f"created:{date_range}"), "repositories")))
    sections["Repository-Dorks"] = repo_dorks

    # ================= CODE =================
    code_dorks = [
        ("Code mentioning term", f'q="{value}", type=code', _search_url(_j(quoted, extra_clause), "code")),
    ]
    if username:
        code_dorks.append((f"Code authored by @{username}", f'user:{username} "{value}"',
                           _search_url(_j(f"user:{username}", quoted), "code")))
    if is_website:
        code_dorks.append((f"Code referencing this domain", f'"{domain}"',
                           _search_url(f'"{domain}"', "code")))
    sections["Code-Dorks"] = code_dorks

    # ================= ISSUES & PULL REQUESTS =================
    issue_dorks = []
    if username:
        issue_dorks += [
            (f"Issues opened by @{username}", f'author:{username}, type=issues',
             _search_url(f"author:{username}", "issues")),
            (f"Pull requests opened by @{username}", f'author:{username} is:pr',
             _search_url(f"author:{username} is:pr", "issues")),
            (f"Issues/PRs commented on by @{username}", f'commenter:{username}',
             _search_url(f"commenter:{username}", "issues")),
        ]
    issue_dorks.append(("Issues/PRs mentioning term", f'q="{value}", type=issues',
                        _search_url(_j(quoted, extra_clause), "issues")))
    sections["Issue-PR-Dorks"] = issue_dorks

    # ================= COMMITS =================
    commit_dorks = [
        ("Commits mentioning term", f'q="{value}", type=commits', _search_url(_j(quoted, extra_clause), "commits")),
    ]
    if username:
        commit_dorks.append((f"Commits authored by @{username}", f'author:{username}',
                             _search_url(f"author:{username}", "commits")))
    if ptype == "Email Address":
        commit_dorks.append((f"Commits by committer email", f'author-email:{value}',
                             _search_url(f"author-email:{value}", "commits")))
    if date_range:
        commit_dorks.append((f"Commits within date range", f'q="{value}" committer-date:{date_range}',
                             _search_url(_j(quoted, f"committer-date:{date_range}"), "commits")))
    sections["Commit-Dorks"] = commit_dorks

    # ================= ORGANIZATIONS =================
    org_dorks = [
        ("Organization search by name", f'q="{value}", type=users, org', _search_url(f"{value} type:org", "users")),
    ]
    sections["Organization-Dorks"] = org_dorks

    # ================= DISCUSSIONS =================
    sections["Discussion-Dorks"] = [
        ("Discussions mentioning term", f'q="{value}", type=discussions', _search_url(_j(quoted, extra_clause), "discussions")),
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