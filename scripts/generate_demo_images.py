"""Generate the illustrated demo property images used by seed data.

Run from the repository root:  python scripts/generate_demo_images.py
Writes SVGs to frontend/public/images/properties/. Local assets keep the demo
working offline and avoid depending on third-party image hosts.
"""

from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "frontend" / "public" / "images" / "properties"

PALETTES = [
    {"sky1": "#dbeafe", "sky2": "#f8fafc", "wall": "#f1f5f9", "accent": "#0f766e", "trim": "#334155", "ground": "#d9f99d"},
    {"sky1": "#fde68a", "sky2": "#fff7ed", "wall": "#fef3c7", "accent": "#b45309", "trim": "#44403c", "ground": "#bbf7d0"},
    {"sky1": "#e0e7ff", "sky2": "#f5f3ff", "wall": "#e2e8f0", "accent": "#4338ca", "trim": "#1e293b", "ground": "#a7f3d0"},
]

W, H = 800, 560


def frame(body: str, p: dict) -> str:
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" role="img">
<defs><linearGradient id="sky" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="{p['sky1']}"/><stop offset="1" stop-color="{p['sky2']}"/></linearGradient></defs>
<rect width="{W}" height="{H}" fill="url(#sky)"/>
<circle cx="660" cy="110" r="46" fill="#ffffff" opacity="0.7"/>
{body}
</svg>
"""


def windows(x0, y0, cols, rows, w, h, gx, gy, fill, frame_color):
    parts = []
    for r in range(rows):
        for c in range(cols):
            x, y = x0 + c * (w + gx), y0 + r * (h + gy)
            lit = (r * 7 + c * 3) % 5 == 0
            parts.append(
                f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="{"#fde68a" if lit else fill}" stroke="{frame_color}" stroke-width="2"/>'
            )
    return "\n".join(parts)


def tree(x, base, scale=1.0):
    return (
        f'<rect x="{x - 6 * scale}" y="{base - 60 * scale}" width="{12 * scale}" height="{60 * scale}" fill="#78350f"/>'
        f'<circle cx="{x}" cy="{base - 80 * scale}" r="{38 * scale}" fill="#15803d"/>'
        f'<circle cx="{x - 22 * scale}" cy="{base - 60 * scale}" r="{26 * scale}" fill="#16a34a"/>'
        f'<circle cx="{x + 24 * scale}" cy="{base - 62 * scale}" r="{24 * scale}" fill="#22c55e"/>'
    )


def apartment(p):
    ground = f'<rect y="470" width="{W}" height="90" fill="{p["ground"]}"/>'
    tower = f'<rect x="250" y="90" width="300" height="380" fill="{p["wall"]}" stroke="{p["trim"]}" stroke-width="3"/>'
    side = f'<rect x="550" y="170" width="120" height="300" fill="{p["wall"]}" stroke="{p["trim"]}" stroke-width="3" opacity="0.85"/>'
    band = f'<rect x="240" y="80" width="320" height="16" fill="{p["accent"]}"/>'
    door = f'<rect x="370" y="400" width="60" height="70" rx="4" fill="{p["accent"]}"/>'
    balconies = "\n".join(
        f'<rect x="262" y="{y}" width="276" height="6" fill="{p["trim"]}" opacity="0.6"/>' for y in range(160, 400, 60)
    )
    body = "\n".join([
        ground, side, windows(565, 190, 3, 7, 24, 28, 12, 12, "#bfdbfe", p["trim"]), tower, band,
        windows(275, 115, 5, 5, 34, 38, 21, 22, "#bfdbfe", p["trim"]), balconies, door,
        tree(160, 470), tree(720, 470, 0.8),
    ])
    return frame(body, p)


def villa(p):
    ground = f'<rect y="460" width="{W}" height="100" fill="{p["ground"]}"/>'
    pool = '<rect x="80" y="490" width="220" height="40" rx="8" fill="#7dd3fc"/>'
    main = f'<rect x="200" y="260" width="420" height="200" fill="{p["wall"]}" stroke="{p["trim"]}" stroke-width="3"/>'
    upper = f'<rect x="300" y="170" width="260" height="90" fill="{p["wall"]}" stroke="{p["trim"]}" stroke-width="3"/>'
    roof = f'<rect x="280" y="150" width="300" height="20" fill="{p["accent"]}"/><rect x="180" y="242" width="460" height="20" fill="{p["accent"]}"/>'
    glass = f'<rect x="230" y="300" width="180" height="120" fill="#bae6fd" stroke="{p["trim"]}" stroke-width="3"/><line x1="290" y1="300" x2="290" y2="420" stroke="{p["trim"]}" stroke-width="2"/><line x1="350" y1="300" x2="350" y2="420" stroke="{p["trim"]}" stroke-width="2"/>'
    door = f'<rect x="480" y="360" width="70" height="100" rx="4" fill="{p["trim"]}"/>'
    body = "\n".join([ground, pool, main, upper, roof, glass, door,
                      windows(330, 190, 3, 1, 50, 50, 30, 0, "#bae6fd", p["trim"]),
                      tree(110, 460), tree(700, 460, 1.1)])
    return frame(body, p)


def house(p):
    ground = f'<rect y="470" width="{W}" height="90" fill="{p["ground"]}"/>'
    walls = f'<rect x="240" y="250" width="320" height="220" fill="{p["wall"]}" stroke="{p["trim"]}" stroke-width="3"/>'
    roof = f'<polygon points="215,255 400,120 585,255" fill="{p["accent"]}" stroke="{p["trim"]}" stroke-width="3"/>'
    attic = f'<circle cx="400" cy="200" r="22" fill="#bfdbfe" stroke="{p["trim"]}" stroke-width="3"/>'
    door = f'<rect x="372" y="380" width="56" height="90" rx="4" fill="{p["trim"]}"/>'
    path = f'<polygon points="372,470 428,470 470,560 330,560" fill="#e7e5e4"/>'
    fence = "\n".join(f'<rect x="{x}" y="440" width="8" height="40" fill="#ffffff" stroke="#a8a29e"/>' for x in range(40, 220, 20))
    body = "\n".join([ground, path, walls, roof, attic, door,
                      windows(270, 280, 2, 2, 60, 46, 20, 26, "#bfdbfe", p["trim"]),
                      windows(450, 280, 1, 2, 70, 46, 0, 26, "#bfdbfe", p["trim"]),
                      fence, tree(660, 470)])
    return frame(body, p)


def living_room(p):
    floor = f'<rect y="400" width="{W}" height="160" fill="#e7e5e4"/><rect width="{W}" height="400" fill="{p["wall"]}"/>'
    window = f'<rect x="90" y="80" width="260" height="220" fill="url(#sky)" stroke="{p["trim"]}" stroke-width="6"/><line x1="220" y1="80" x2="220" y2="300" stroke="{p["trim"]}" stroke-width="4"/>'
    sofa = f'<rect x="380" y="300" width="320" height="110" rx="18" fill="{p["accent"]}"/><rect x="360" y="330" width="40" height="90" rx="12" fill="{p["accent"]}"/><rect x="680" y="330" width="40" height="90" rx="12" fill="{p["accent"]}"/><rect x="400" y="270" width="280" height="60" rx="14" fill="{p["accent"]}" opacity="0.85"/>'
    table = f'<rect x="200" y="430" width="200" height="16" rx="6" fill="{p["trim"]}"/><rect x="220" y="446" width="10" height="40" fill="{p["trim"]}"/><rect x="370" y="446" width="10" height="40" fill="{p["trim"]}"/>'
    rug = '<ellipse cx="400" cy="490" rx="300" ry="40" fill="#d6d3d1"/>'
    lamp = f'<rect x="733" y="200" width="6" height="210" fill="{p["trim"]}"/><polygon points="706,200 766,200 752,160 720,160" fill="#fde68a"/>'
    art = f'<rect x="470" y="110" width="150" height="100" fill="#ffffff" stroke="{p["trim"]}" stroke-width="4"/><polygon points="480,200 530,140 570,180 610,150 610,200" fill="{p["accent"]}" opacity="0.6"/>'
    plant = '<rect x="50" y="360" width="40" height="50" fill="#a8a29e"/><circle cx="70" cy="340" r="30" fill="#16a34a"/>'
    return frame("\n".join([floor, window, rug, sofa, table, lamp, art, plant]), p)


def bedroom(p):
    floor = f'<rect y="400" width="{W}" height="160" fill="#d6d3d1"/><rect width="{W}" height="400" fill="{p["wall"]}"/>'
    bed = f'<rect x="220" y="230" width="360" height="40" rx="10" fill="{p["trim"]}"/><rect x="200" y="300" width="400" height="120" rx="14" fill="#ffffff" stroke="{p["trim"]}" stroke-width="3"/><rect x="200" y="340" width="400" height="80" rx="10" fill="{p["accent"]}" opacity="0.8"/><rect x="240" y="276" width="120" height="40" rx="14" fill="#f5f5f4"/><rect x="440" y="276" width="120" height="40" rx="14" fill="#f5f5f4"/>'
    side = f'<rect x="90" y="330" width="80" height="90" rx="6" fill="{p["trim"]}" opacity="0.8"/><rect x="630" y="330" width="80" height="90" rx="6" fill="{p["trim"]}" opacity="0.8"/><circle cx="130" cy="310" r="18" fill="#fde68a"/><circle cx="670" cy="310" r="18" fill="#fde68a"/>'
    window = f'<rect x="300" y="60" width="200" height="140" fill="url(#sky)" stroke="{p["trim"]}" stroke-width="6"/>'
    return frame("\n".join([floor, window, bed, side]), p)


def kitchen(p):
    floor = f'<rect y="420" width="{W}" height="140" fill="#e7e5e4"/><rect width="{W}" height="420" fill="{p["wall"]}"/>'
    upper = "\n".join(f'<rect x="{x}" y="70" width="110" height="110" rx="6" fill="{p["accent"]}" opacity="0.85"/>' for x in range(80, 720, 125))
    counter = f'<rect x="60" y="300" width="680" height="24" fill="{p["trim"]}"/><rect x="70" y="324" width="660" height="100" fill="{p["accent"]}"/>'
    hob = '<rect x="300" y="290" width="140" height="10" fill="#1f2937"/><circle cx="335" cy="295" r="8" fill="#ef4444"/><circle cx="405" cy="295" r="8" fill="#ef4444"/>'
    tiles = "\n".join(f'<rect x="{x}" y="200" width="40" height="40" fill="#ffffff" stroke="#e5e7eb"/>' for x in range(60, 740, 40)) + "\n" + "\n".join(f'<rect x="{x}" y="240" width="40" height="40" fill="#ffffff" stroke="#e5e7eb"/>' for x in range(60, 740, 40))
    handles = "\n".join(f'<rect x="{x}" y="360" width="30" height="6" rx="3" fill="#f8fafc"/>' for x in range(110, 720, 125))
    return frame("\n".join([floor, upper, tiles, counter, hob, handles]), p)


SCENES = {"apartment": apartment, "villa": villa, "house": house,
          "living": living_room, "bedroom": bedroom, "kitchen": kitchen}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, draw in SCENES.items():
        for index, palette in enumerate(PALETTES, start=1):
            (OUT / f"{name}-{index}.svg").write_text(draw(palette))
    print(f"Wrote {len(SCENES) * len(PALETTES)} images to {OUT}")


if __name__ == "__main__":
    main()
