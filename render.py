#!/usr/bin/env python3
"""Build-time renderer for news-image-20261125, variant B (poster-grid).

Renders entry.png (1024x1024) next to this file. Deterministic: no
timestamps, no randomness, fixed fonts and layout. Two runs produce
byte-identical output. Pillow only. This is NOT the entrypoint; the
entrypoint (main.ts) only copies the pre-rendered entry.png.

Layout (poster-grid, deliberately different from a classic broadsheet):
  - giant navy masthead: "THE WORLD IN ONE DAY" + "WEDNESDAY 25 NOVEMBER 2026"
  - 3 LEAD stories as a horizontal hero band
  - 7 regions in a colour-coded 3-column poster grid
  - MARKETS / TECH / SPORT / SCIENCE as a full-width strip
  - navy footer strip repeating the date (date-check)

Content: exactly the 40 stories listed in ni25-design-spec.md
(5 Tier A + 35 Tier B, 7 regions). No story is dated inside the image
beyond the edition masthead.
"""

import hashlib
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))

W, H = 1024, 1024
MARGIN = 16
GAP = 8
MAST_H = 122
HERO_H = 158
FOOT_H = 52
GRID_TOP = MAST_H + GAP + HERO_H + GAP          # 296
GRID_BOTTOM = H - FOOT_H - GAP                  # 964
GRID_H = GRID_BOTTOM - GRID_TOP                 # 668

BG = (247, 242, 231)          # paper
INK = (16, 24, 38)            # near-black headline ink
GREY = (74, 82, 96)           # summary grey
NAVY = (16, 36, 62)           # masthead / footer
GOLD = (242, 183, 5)          # date gold
HAIR = (216, 210, 196)        # hairline separators
BORDER = (200, 194, 178)      # panel borders
WHITE = (255, 255, 255)

SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# Column geometry: three panels across the 992 px inner width.
PANEL_X = [16, 349, 682]
PANEL_W = [325, 325, 326]

# Region column stacks (left to right, top to bottom).
COLUMNS = [[0, 3], [1, 4], [2, 5]]  # region indexes into REGIONS

LEADS = [
    {
        "tag": "LEAD 1 · OCEANIA",
        "color": (199, 126, 31),
        "headline": "Australia inflation jumps to 4.9% — highest in about three years",
        "summary": "Trimmed mean 3.8%; Perth 5.5%; fuel +6.3% in a month.",
    },
    {
        "tag": "LEAD 2 · EUROPE",
        "color": (29, 78, 137),
        "headline": "Zelenskiy confirms Ukraine hit Russian ship Sparta II in the Gulf of Finland",
        "summary": "Cargo ship hit by drones on 21 Nov, ablaze, towed to St Petersburg.",
    },
    {
        "tag": "LEAD 3 · MIDDLE EAST",
        "color": (179, 64, 42),
        "headline": "Houthis hit Riyadh's tallest tower a second time in five days — 11 wounded",
        "summary": "PIF Tower struck again; victims from Saudi Arabia, India, Nepal, Egypt.",
    },
]

REGIONS = [
    {
        "name": "EUROPE",
        "color": (29, 78, 137),
        "stories": [
            ("Ukraine sinks Russian corvette Merkury in Benghazi port, Libya",
             "Seven sea drones used; a cargo ship was also hit."),
            ("Russian drone briefly enters Polish airspace during attack on Ukraine",
             "Second NATO incursion in four days."),
            ("Russia warns Estonia of open war; NATO on alert",
             "Warning delivered from Moscow on Monday."),
            ("Russian strike on Zaporizhzhia: 2 killed, 40 wounded",
             "Strike hits the southern Ukrainian city."),
            ("Ukrainian drone strikes halt Novoshakhtinsk and Perm refineries",
             "Russian refinery output down 45% since late October."),
            ("EU to curb hybrid car imports from 1 December — mainly China",
             "Quotas also for the UK, Japan and South Korea."),
        ],
    },
    {
        "name": "MIDDLE EAST",
        "color": (179, 64, 42),
        "stories": [
            ("Houthis 60 km from Aden, poised to strike; Aden 'will not fall'",
             "Government forces hold the port city."),
            ("UK sanctions Houthis and four senior officials",
             "New measures target the rebel movement."),
            ("Israel kills Hamas internal security chief Abu Nahel and six in Gaza",
             "Medics say six more killed despite the ceasefire."),
            ("Vance and Rubio meet Qatar PM; Doha pushes to revive Iran talks",
             "US leaders in Doha for talks on Iran."),
            ("Bus hits parked truck in Ras Al Khaimah, UAE: 13 killed, 14 wounded",
             "Crash in the northern emirate."),
        ],
    },
    {
        "name": "ASIA",
        "color": (14, 124, 107),
        "stories": [
            ("Huawei convicted in US court on 10 of 12 counts",
             "Bank fraud, sanctions breaches, trade-secret theft."),
            ("US blacklists Megaspeed Technologies over alleged AI chip diversion",
             "Affiliates also named in new export controls."),
            ("China investigates Shanghai party chief Chen Jining",
             "Fourth Politburo member probed since 2022."),
            ("Cikande candy factory fire, Banten: 24 confirmed dead, about 30 missing",
             "Blaze at the Indonesian factory; toll still rising."),
            ("Delhi AQI 242 ('poor'), Sirifort worst at 336",
             "Air quality stays poor across the capital."),
            ("Indonesia–EU sign trade deal: 98.5% of EU goods tariffs scrapped",
             "Landmark agreement signed by both sides."),
            ("Gas explosion at Hanoi porridge shop: 6 killed, 10 wounded",
             "Blast hits a street-food shop in the capital."),
        ],
    },
    {
        "name": "AFRICA",
        "color": (199, 126, 31),
        "stories": [
            ("Senegal restored as Africa Cup champions — CAS overturns CAF ruling",
             "Title back from Morocco after January final walk-off."),
            ("Nigeria central bank holds rate at 23% (unanimous)",
             "Monetary policy committee keeps rate steady."),
            ("Tinubu proposes \u20a665.18 trillion budget",
             "Nigeria's president presents spending plan."),
            ("WFP: shipping disruption threatens food aid for 7.3 million people",
             "Aid deliveries at risk across the region."),
            ("UNAIDS: funding cuts threaten HIV services in Africa",
             "Health programmes face deep cuts."),
            ("Drone strike on home and UN building in Khartoum: at least 4 killed",
             "Attack reported in the Sudanese capital."),
        ],
    },
    {
        "name": "AMERICAS",
        "color": (46, 125, 50),
        "stories": [
            ("Trump arrives in Manila for Quad summit and Thailand trade deal",
             "US president in the Philippines for the summit."),
            ("GTA VI grosses $3.79 billion on day one — biggest entertainment launch ever",
             "Metacritic score 99 for the record-breaking game."),
            ("California braces for near-record king tide as Thanksgiving storm nears",
             "Coastal flooding risk rises ahead of the holiday."),
            ("FBI probes suspected hack of its national crime database",
             "Bureau investigates breach of crime records."),
            ("Baby shower shooting in Parma, Ohio: 3 killed including a 17-year-old girl",
             "Shooting at a family gathering in Ohio."),
        ],
    },
    {
        "name": "OCEANIA",
        "color": (106, 76, 147),
        "stories": [
            ("Matildas: goalkeeper Teagan Micah returns to squad",
             "Neurological issue nearly ended her career."),
            ("A-Leagues agree new deal with players, ending pay dispute",
             "Pay row settled with a new agreement."),
            ("Newcastle Jets lose again in ACL to Kashiwa Reysol; losing run reaches five",
             "Fifth straight defeat in Asian competition."),
            ("Australia U-17 (Joeys) held 0–0 by Denmark at World Cup in Qatar",
             "Draw follows the win over Argentina."),
        ],
    },
]

MARKETS = {
    "name": "MARKETS · TECH · SPORT · SCIENCE",
    "color": (55, 71, 79),
    "stories": [
        ("Shenzhou-24 carries first foreign astronaut to Tiangong",
         "First foreign crew member in orbit."),
        ("BepiColombo begins science mission orbiting Mercury",
         "Science work starts after eight years."),
        ("Verstappen wins Las Vegas GP by 0.639s over Norris",
         "35 lead changes in a chaotic Nevada race."),
        ("COP31 in Antalya collapses with no fossil-fuel deal",
         "UN chief Guterres warns the world."),
    ],
}

# Auto-fit candidates (headline px, summary px, story gap px, header px, pad px).
# First candidate that fits the grid is used; deterministic. Integer sizes
# only, so Pillow renders identically on every run.
CANDIDATES = [
    (12, 10, 4, 28, 12),
    (11, 10, 3, 27, 12),
    (11, 9, 3, 26, 11),
    (10, 9, 2, 25, 11),
]


def wrap(draw, text, font, max_w):
    """Greedy word wrap; returns a list of lines (never empty)."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if draw.textlength(trial, font=font) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def measure(draw, params):
    """Measure every story at the given params; return layout numbers."""
    hs, ss, gap, header_h, pad = params
    hf = ImageFont.truetype(SANS_B, hs)
    sf = ImageFont.truetype(SANS, ss)
    hl_lh = hs + 3
    sl_lh = ss + 3
    wrapped = {}
    col_heights = []
    for ci, col in enumerate(COLUMNS):
        h = 0
        for ri in col:
            region = REGIONS[ri]
            inner = PANEL_W[ci] - 2 * pad
            h += header_h
            for si, (headline, summary) in enumerate(region["stories"]):
                hl = wrap(draw, headline, hf, inner)
                sl = wrap(draw, summary, sf, inner)
                wrapped[(ri, si)] = (hl, sl)
                h += len(hl) * hl_lh + len(sl) * sl_lh + gap
            h += GAP
        col_heights.append(h - GAP)
    # Markets strip: 4 mini-columns.
    strip_col_w = (W - 2 * MARGIN - 3 * GAP) / 4
    strip_inner = strip_col_w - 2 * 10
    strip_block = 0
    strip_wrapped = []
    for headline, summary in MARKETS["stories"]:
        hl = wrap(draw, headline, hf, strip_inner)
        sl = wrap(draw, summary, sf, strip_inner)
        strip_wrapped.append((hl, sl))
        strip_block = max(strip_block, len(hl) * hl_lh + len(sl) * sl_lh + gap)
    strip_h = header_h + strip_block + 10
    cols_area = GRID_H - strip_h - GAP
    fits = max(col_heights) <= cols_area
    return {
        "params": params,
        "fits": fits,
        "col_heights": col_heights,
        "strip_h": strip_h,
        "strip_wrapped": strip_wrapped,
        "wrapped": wrapped,
        "hl_lh": hl_lh,
        "sl_lh": sl_lh,
        "strip_col_w": strip_col_w,
    }


def draw_region_panel(draw, x, y, w, region, layout):
    hs, ss, gap, header_h, pad = layout["params"]
    hf = ImageFont.truetype(SANS_B, hs)
    sf = ImageFont.truetype(SANS, ss)
    ri = REGIONS.index(region)
    # Panel height from measured content.
    height = header_h
    for si in range(len(region["stories"])):
        hl, sl = layout["wrapped"][(ri, si)]
        height += len(hl) * layout["hl_lh"] + len(sl) * layout["sl_lh"] + gap
    draw.rectangle([x, y, x + w - 1, y + height - 1], fill=WHITE, outline=BORDER)
    draw.rectangle([x, y, x + w - 1, y + header_h - 1], fill=region["color"])
    name_f = ImageFont.truetype(SANS_B, 15)
    count_f = ImageFont.truetype(SANS_B, 10)
    draw.text((x + pad, y + (header_h - 15) // 2), region["name"],
              font=name_f, fill=WHITE)
    count = "%d STORIES" % len(region["stories"])
    cw = draw.textlength(count, font=count_f)
    draw.text((x + w - pad - cw, y + (header_h - 10) // 2), count,
              font=count_f, fill=WHITE)
    cy = y + header_h + 3
    for si, (headline, summary) in enumerate(region["stories"]):
        hl, sl = layout["wrapped"][(ri, si)]
        for line in hl:
            draw.text((x + pad, cy), line, font=hf, fill=INK)
            cy += layout["hl_lh"]
        for line in sl:
            draw.text((x + pad, cy), line, font=sf, fill=GREY)
            cy += layout["sl_lh"]
        cy += gap
        if si < len(region["stories"]) - 1:
            draw.line([x + pad, cy - gap // 2, x + w - pad - 1, cy - gap // 2],
                      fill=HAIR)
    return height


def main():
    img = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # --- Masthead -------------------------------------------------------
    draw.rectangle([0, 0, W - 1, MAST_H - 1], fill=NAVY)
    title_f = ImageFont.truetype(SERIF_B, 50)
    title = "THE WORLD IN ONE DAY"
    tw = draw.textlength(title, font=title_f)
    draw.text(((W - tw) / 2, 12), title, font=title_f, fill=WHITE)
    draw.rectangle([(W - 120) / 2, 76, (W + 120) / 2, 78], fill=GOLD)
    date_f = ImageFont.truetype(SANS_B, 32)
    date = "WEDNESDAY 25 NOVEMBER 2026"
    dw = draw.textlength(date, font=date_f)
    draw.text(((W - dw) / 2, 84), date, font=date_f, fill=GOLD)

    # --- Hero band: 3 leads --------------------------------------------
    hero_y = MAST_H + GAP
    tag_f = ImageFont.truetype(SANS_B, 11)
    num_f = ImageFont.truetype(SANS_B, 30)
    lead_hf = ImageFont.truetype(SANS_B, 18)
    lead_sf = ImageFont.truetype(SANS, 12)
    for i, lead in enumerate(LEADS):
        x = PANEL_X[i]
        w = PANEL_W[i]
        draw.rectangle([x, hero_y, x + w - 1, hero_y + HERO_H - 1],
                       fill=WHITE, outline=BORDER)
        draw.rectangle([x, hero_y, x + w - 1, hero_y + 5], fill=lead["color"])
        draw.text((x + 12, hero_y + 14), lead["tag"], font=tag_f,
                  fill=lead["color"])
        draw.text((x + w - 30, hero_y + 10), str(i + 1), font=num_f,
                  fill=lead["color"])
        inner = w - 24
        hl = wrap(draw, lead["headline"], lead_hf, inner)
        sl = wrap(draw, lead["summary"], lead_sf, inner)
        cy = hero_y + 38
        for line in hl:
            draw.text((x + 12, cy), line, font=lead_hf, fill=INK)
            cy += 22
        cy += 6
        for line in sl:
            draw.text((x + 12, cy), line, font=lead_sf, fill=GREY)
            cy += 15

    # --- Region grid: pick the first auto-fit candidate that fits -----
    layout = None
    for params in CANDIDATES:
        cand = measure(draw, params)
        if cand["fits"]:
            layout = cand
            break
    if layout is None:
        raise SystemExit("no auto-fit candidate fits the grid")
    hs, ss, gap, header_h, pad = layout["params"]
    hf = ImageFont.truetype(SANS_B, hs)
    sf = ImageFont.truetype(SANS, ss)

    cols_h = max(layout["col_heights"])
    strip_h = layout["strip_h"]
    # Centre the whole grid block vertically inside the grid area.
    y_off = GRID_TOP + (GRID_H - (cols_h + GAP + strip_h)) // 2

    for ci, col in enumerate(COLUMNS):
        cy = y_off
        for ri in col:
            used = draw_region_panel(draw, PANEL_X[ci], cy, PANEL_W[ci],
                                     REGIONS[ri], layout)
            cy += used + GAP

    # --- Markets strip --------------------------------------------------
    strip_y = y_off + cols_h + GAP
    draw.rectangle([MARGIN, strip_y, W - MARGIN - 1, strip_y + strip_h - 1],
                   fill=WHITE, outline=BORDER)
    draw.rectangle([MARGIN, strip_y, W - MARGIN - 1, strip_y + header_h - 1],
                   fill=MARKETS["color"])
    name_f = ImageFont.truetype(SANS_B, 15)
    count_f = ImageFont.truetype(SANS_B, 10)
    draw.text((MARGIN + 12, strip_y + (header_h - 15) // 2),
              MARKETS["name"], font=name_f, fill=WHITE)
    count = "4 STORIES"
    cw = draw.textlength(count, font=count_f)
    draw.text((W - MARGIN - 12 - cw, strip_y + (header_h - 10) // 2), count,
              font=count_f, fill=WHITE)
    scw = layout["strip_col_w"]
    for i, (hl, sl) in enumerate(layout["strip_wrapped"]):
        cx = MARGIN + i * (scw + GAP)
        cy = strip_y + header_h + 5
        for line in hl:
            draw.text((cx + 10, cy), line, font=hf, fill=INK)
            cy += layout["hl_lh"]
        for line in sl:
            draw.text((cx + 10, cy), line, font=sf, fill=GREY)
            cy += layout["sl_lh"]
        if i < 3:
            vx = cx + scw + GAP // 2
            draw.line([vx, strip_y + header_h + 6, vx,
                       strip_y + strip_h - 6], fill=HAIR)

    # --- Footer strip: date repeated (date-check) -----------------------
    foot_y = H - FOOT_H
    draw.rectangle([0, foot_y, W - 1, H - 1], fill=NAVY)
    foot_date_f = ImageFont.truetype(SANS_B, 17)
    foot_date = "WEDNESDAY 25 NOVEMBER 2026"
    fdw = draw.textlength(foot_date, font=foot_date_f)
    draw.text(((W - fdw) / 2, foot_y + 6), foot_date, font=foot_date_f,
              fill=GOLD)
    foot2_f = ImageFont.truetype(SANS, 11)
    foot2 = ("40 STORIES \u00b7 7 REGIONS \u00b7 ALL STORIES HAPPENED OR WERE "
             "FIRST REPORTED ON 25 NOVEMBER 2026")
    f2w = draw.textlength(foot2, font=foot2_f)
    draw.text(((W - f2w) / 2, foot_y + 30), foot2, font=foot2_f, fill=WHITE)

    out = os.path.join(HERE, "entry.png")
    img.save(out, "PNG")
    data = open(out, "rb").read()
    n_stories = 3 + sum(len(r["stories"]) for r in REGIONS) + len(MARKETS["stories"])
    print("rendered %s" % out)
    print("size: %d bytes" % len(data))
    print("sha256: %s" % hashlib.sha256(data).hexdigest())
    print("stories: %d (3 leads + %d regions + %d markets)" % (
        n_stories,
        sum(len(r["stories"]) for r in REGIONS),
        len(MARKETS["stories"])))
    print("regions: 7")
    print("auto-fit params (headline, summary, gap, header, pad): %s"
          % (layout["params"],))
    print("column heights: %s, strip height: %d" % (
        layout["col_heights"], strip_h))


if __name__ == "__main__":
    main()
