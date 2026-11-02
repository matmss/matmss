#!/usr/bin/env python3
"""Render the static hero banners. Run by hand when the wording changes."""
import pathlib

OUT = pathlib.Path(__file__).resolve().parent.parent / "assets"
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"
MONO = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
THEMES = {
    "dark": dict(top="#0b1220", bottom="#10243f", ink="#f0f6fc", sub="#c3c2b7",
                 accent="#58a6ff", ring="#58a6ff", border="#30363d"),
    "light": dict(top="#f6f9fe", bottom="#dfeafa", ink="#0b1220", sub="#3d4450",
                  accent="#1f65bd", ring="#2a78d6", border="#d0d7de"),
}


def hero(t):
    rings = "".join(
        f'<circle cx="700" cy="110" r="{r}" fill="none" stroke="{t["ring"]}" '
        f'stroke-opacity="{o}"/>'
        for r, o in ((40, .55), (80, .38), (120, .24), (160, .14), (200, .08))
    )
    blips = "".join(
        f'<circle cx="{x}" cy="{y}" r="{r}" fill="{t["accent"]}"/>'
        for x, y, r in ((700, 110, 5), (742, 72, 4), (640, 150, 3.5), (778, 158, 3), (626, 58, 3))
    )
    sweep = (f'<path d="M700 110 L700 -50 A160 160 0 0 1 838 30 Z" '
             f'fill="url(#sweep)"/>')
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="840" height="220" viewBox="0 0 840 220" role="img" aria-label="Matheus Santos. Senior QA Engineer, SDET, API and backend.">
<defs>
<linearGradient id="bg" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{t['top']}"/><stop offset="1" stop-color="{t['bottom']}"/></linearGradient>
<linearGradient id="sweep" x1="0" y1="1" x2="1" y2="0"><stop offset="0" stop-color="{t['ring']}" stop-opacity=".28"/><stop offset="1" stop-color="{t['ring']}" stop-opacity="0"/></linearGradient>
<clipPath id="card"><rect width="840" height="220" rx="12"/></clipPath>
</defs>
<g clip-path="url(#card)">
<rect width="840" height="220" fill="url(#bg)"/>
{rings}{sweep}{blips}
</g>
<rect x=".5" y=".5" width="839" height="219" rx="12" fill="none" stroke="{t['border']}"/>
<text x="36" y="66" font-family="{MONO}" font-size="14" fill="{t['accent']}">Curitiba, Brazil</text>
<text x="36" y="112" font-family="{FONT}" font-size="42" font-weight="700" fill="{t['ink']}">Matheus Santos</text>
<text x="36" y="148" font-family="{FONT}" font-size="19" font-weight="500" fill="{t['ink']}">Senior QA Engineer · SDET · API &amp; Backend</text>
<text x="36" y="178" font-family="{FONT}" font-size="15" fill="{t['sub']}">Systems that run themselves, and the tests that prove they work.</text>
</svg>
"""


for name, theme in THEMES.items():
    (OUT / f"hero-{name}.svg").write_text(hero(theme), encoding="utf-8")
