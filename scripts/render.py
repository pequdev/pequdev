#!/usr/bin/env python3
"""Render README.md: the MAGI boot panel (magi.txt) beside a character
sheet, with live GitHub stats when GITHUB_TOKEN is set. Plain ASCII only, so
every line keeps its width in GitHub's monospace fonts.
Usage: GITHUB_TOKEN=… GH_USER=pequdev python3 scripts/render.py"""
import datetime, json, os, urllib.request

USER = os.environ.get("GH_USER", "pequdev")
TOKEN = os.environ.get("GITHUB_TOKEN")
QUERY = """query($login: String!) { user(login: $login) {
  createdAt followers { totalCount }
  contributionsCollection { contributionCalendar { totalContributions } } } }"""


def stats():
    if not TOKEN:
        return {"xp": "?", "party": "?", "days": "?", "since": "?"}
    body = json.dumps({"query": QUERY, "variables": {"login": USER}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=body, headers={
        "Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"})
    user = json.load(urllib.request.urlopen(req))["data"]["user"]
    born = datetime.datetime.fromisoformat(user["createdAt"].replace("Z", "+00:00"))
    return {
        "xp": user["contributionsCollection"]["contributionCalendar"]["totalContributions"],
        "party": user["followers"]["totalCount"],
        "days": (datetime.datetime.now(datetime.timezone.utc) - born).days,
        "since": born.year,
    }


def dots(label, value, width=38):
    value = str(value)
    return f"{label} {'.' * (width - len(label) - len(value) - 2)} {value}"


def bar(name, score, note):
    filled = round(score / 2)
    return f"{name} {score:>2} [{'#' * filled}{'-' * (10 - filled)}] {note}"


s = stats()
sheet = [
    'MACIEJ "PEQU" PIERNIKOWSKI',
    "=" * 38,
    dots("Race", "Human (Polish)"),
    dots("Class", "Product Designer / AI Engineer"),
    dots("Alignment", "Chaotic Good"),
    dots("Home", "Berlin, since 2011"),
    dots("Level", "20+ (since the early 2000s)"),
    "",
    "ABILITY SCORES",
    "-" * 38,
    bar("STR", 12, "ships on deadline"),
    bar("DEX", 17, "Figma to React"),
    bar("CON", 18, "print to DeFi"),
    bar("INT", 18, "Bayes, hyperplanes"),
    bar("WIS", 17, "in data we trust"),
    bar("CHA", 16, "let's play techno"),
    "",
    "PROFICIENCIES",
    "-" * 38,
    "+ End-to-End Product Design",
    "+ UX Audit & Research",
    "+ Design Engineering",
    "+ AI Systems",
    "+ E-commerce, SaaS & Fintech, Web3",
    "",
    "INVENTORY",
    "-" * 38,
    "Figma, React, TypeScript, Claude Code,",
    "Codex, Terraform, Google Cloud",
    "",
    "GITHUB STATS",
    "-" * 38,
    dots("XP (contributions, past year)", s["xp"]),
    dots("Party (followers)", s["party"]),
    dots("Days on GitHub", s["days"]),
    dots("Adventuring since", s["since"]),
    "",
    "QUEST LOG",
    "-" * 38,
    "> pequ.dev: case studies since 2006",
]
art = open("magi.txt").read().rstrip("\n").splitlines()
width = max(len(line) for line in art)
top = 1
rows = []
for i in range(max(len(art), len(sheet) + top)):
    a = art[i] if i < len(art) else ""
    t = sheet[i - top] if 0 <= i - top < len(sheet) else ""
    rows.append((a.ljust(width) + "  " + t).rstrip())
text = "\n".join(rows)
assert all(ord(c) < 128 for c in text), "non-ASCII would break the columns"
assert "<" not in text, "a < would be read as HTML inside <pre>"
with open("README.md", "w") as f:
    f.write("<!-- Character sheet. Rendered by scripts/render.py; stats refresh daily. -->\n")
    f.write("<pre>\n" + text.replace("&", "&amp;") + "\n</pre>\n")
