#!/usr/bin/env python3
"""Render assets/stats-{dark,light}.svg from live GitHub data.

Run by .github/workflows/stats.yml. Standard library only.
Needs GITHUB_TOKEN; GITHUB_LOGIN defaults to the profile owner.
"""
import json
import os
import pathlib
import urllib.request
from datetime import date, datetime, timezone
from html import escape

LOGIN = os.environ.get("GITHUB_LOGIN", "matmss")
OUT = pathlib.Path(__file__).resolve().parent.parent / "assets"

QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    repositories(first: 100, ownerAffiliations: OWNER, privacy: PUBLIC, isFork: false) {
      totalCount
      nodes {
        name
        languages(first: 12, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
    contributionsCollection {
      totalPullRequestContributions
      contributionCalendar {
        totalContributions
        weeks { contributionDays { contributionCount } }
      }
    }
  }
}"""

# Each language keeps its hue across runs, so colour follows the language
# rather than its rank. Anything unlisted folds into "Other".
# Slots are the validated categorical palette, in order.
LANGUAGE_SLOTS = ["Python", "JavaScript", "Kotlin", "Java", "C++"]
THEMES = {
    "dark": {
        "surface": "#0d1117", "border": "#30363d", "primary": "#f0efec",
        "secondary": "#c3c2b7", "muted": "#8b949e", "other": "#6e7681",
        "bars": "#3987e5", "empty": "#21262d",
        "series": ["#3987e5", "#d95926", "#199e70", "#c98500", "#d55181"],
    },
    "light": {
        "surface": "#fcfcfb", "border": "#d0d7de", "primary": "#0b0b0b",
        "secondary": "#52514e", "muted": "#656d76", "other": "#8c959f",
        "bars": "#2a78d6", "empty": "#eaeef2",
        "series": ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"],
    },
}
WIDTH = 840
PAD = 24
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"


def fetch():
    body = json.dumps({"query": QUERY, "variables": {"login": LOGIN}}).encode()
    request = urllib.request.Request(
        "https://api.github.com/graphql",
        data=body,
        headers={
            "Authorization": f"bearer {os.environ['GITHUB_TOKEN']}",
            "Content-Type": "application/json",
            "User-Agent": f"{LOGIN}-profile-stats",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.load(response)
    if "errors" in payload:
        raise SystemExit(f"GitHub API error: {payload['errors']}")
    return payload["data"]["user"]


def summarise(user):
    calendar = user["contributionsCollection"]["contributionCalendar"]
    weeks = [
        sum(day["contributionCount"] for day in week["contributionDays"])
        for week in calendar["weeks"]
    ]
    sizes = {}
    for repo in user["repositories"]["nodes"]:
        if repo["name"] == LOGIN:  # this repo's generator is not a project
            continue
        for edge in repo["languages"]["edges"]:
            name = edge["node"]["name"]
            sizes[name] = sizes.get(name, 0) + edge["size"]

    # Markup and build files say little about what someone engineers with.
    ignored = {"HTML", "CSS", "EJS", "TeX", "Makefile", "Dockerfile", "Shell",
               "PowerShell", "Gherkin", "Batchfile"}
    total = sum(size for name, size in sizes.items() if name not in ignored)
    languages = [
        (name, sizes[name] / total) for name in LANGUAGE_SLOTS if sizes.get(name)
    ]
    other = 1 - sum(share for _, share in languages)
    if other > 0.0005:
        languages.append(("Other", other))

    joined = datetime.fromisoformat(user["createdAt"].replace("Z", "+00:00"))
    years = (datetime.now(timezone.utc) - joined).days // 365
    return {
        "tiles": [
            (f"{calendar['totalContributions']:,}", "Contributions, past year"),
            (str(user["contributionsCollection"]["totalPullRequestContributions"]),
             "Pull requests, past year"),
            (str(user["repositories"]["totalCount"]), "Public repositories"),
            (f"{years}+", "Years on GitHub"),
        ],
        "weeks": weeks,
        "languages": languages,
    }


def text(x, y, value, size, fill, weight=400, anchor="start"):
    return (f'<text x="{x:.1f}" y="{y}" font-size="{size}" font-weight="{weight}" '
            f'fill="{fill}" text-anchor="{anchor}">{escape(value)}</text>')


def render(stats, theme):
    inner = WIDTH - 2 * PAD
    parts = []

    # Headline tiles
    tile_width = inner / len(stats["tiles"])
    for index, (value, label) in enumerate(stats["tiles"]):
        x = PAD + index * tile_width
        parts.append(text(x, 62, value, 32, theme["primary"], 600))
        parts.append(text(x, 84, label, 13, theme["muted"]))

    # Weekly contributions: one series, so the title names it and no legend.
    parts.append(text(PAD, 124, "Weekly contributions", 13, theme["secondary"], 600))
    weeks = stats["weeks"]
    chart_top, chart_height = 136, 56
    peak = max(max(weeks), 1)
    step = inner / len(weeks)
    bar_width = max(step - 2, 2)
    for index, count in enumerate(weeks):
        height = max(chart_height * count / peak, 3)
        x = PAD + index * step
        y = chart_top + chart_height - height
        fill = theme["bars"] if count else theme["empty"]
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{bar_width:.1f}" '
            f'height="{height:.1f}" rx="{min(2, height / 2):.1f}" fill="{fill}">'
            f'<title>{count} contributions</title></rect>'
        )

    # Language share: thin segmented bar, labelled so colour is never alone.
    parts.append(text(PAD, 224, "Languages in public repositories", 13,
                      theme["secondary"], 600))
    x = float(PAD)
    gap = 2
    usable = inner - gap * (len(stats["languages"]) - 1)
    colors = []
    for name, share in stats["languages"]:
        color = (theme["other"] if name == "Other"
                 else theme["series"][LANGUAGE_SLOTS.index(name)])
        colors.append(color)
        width = max(usable * share, 2)
        parts.append(f'<rect x="{x:.1f}" y="236" width="{width:.1f}" height="8" '
                     f'rx="4" fill="{color}"><title>{escape(name)} '
                     f'{share:.0%}</title></rect>')
        x += width + gap

    x = float(PAD)
    for (name, share), color in zip(stats["languages"], colors):
        label = f"{name} {share:.0%}" if share >= 0.005 else f"{name} <1%"
        parts.append(f'<circle cx="{x + 5:.1f}" cy="266" r="5" fill="{color}"/>')
        parts.append(text(x + 16, 271, label, 13, theme["secondary"]))
        x += 16 + len(label) * 7.1 + 18

    updated = date.today().isoformat()
    parts.append(text(WIDTH - PAD, 302, f"Updated {updated} · public activity",
                      11, theme["muted"], anchor="end"))

    height = 318
    summary = ", ".join(f"{label}: {value}" for value, label in stats["tiles"])
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" '
        f'viewBox="0 0 {WIDTH} {height}" role="img" aria-label="{escape(summary)}" '
        f'font-family="{FONT}">'
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="12" '
        f'fill="{theme["surface"]}" stroke="{theme["border"]}"/>'
        + "".join(parts) + "</svg>\n"
    )


def main():
    stats = summarise(fetch())
    OUT.mkdir(exist_ok=True)
    for name, theme in THEMES.items():
        (OUT / f"stats-{name}.svg").write_text(render(stats, theme), encoding="utf-8")
    print(stats["tiles"], stats["languages"])


if __name__ == "__main__":
    main()
