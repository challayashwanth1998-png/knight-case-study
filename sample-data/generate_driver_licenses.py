ok """
Generate realistic-looking CDL (Commercial Driver License) card images for 5 test drivers.
Creates individual PNG files + a combined PDF for the AI pipeline to process.
"""
import os
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = os.path.join(os.path.dirname(__file__), "perfect-submission", "driver-licenses")
os.makedirs(OUT_DIR, exist_ok=True)

CARD_W, CARD_H = 675, 425

# Colors
NAVY = (30, 58, 138)
DARK_BLUE = (15, 30, 80)
LIGHT_BLUE = (200, 220, 255)
WHITE = (255, 255, 255)
BLACK = (20, 20, 20)
GOLD = (218, 165, 32)
RED = (180, 30, 30)
LIGHT_GRAY = (240, 240, 245)
MEDIUM_GRAY = (150, 150, 160)

STATE_INFO = {
    "TN": {"name": "TENNESSEE", "color": (0, 100, 60), "accent": (255, 200, 0)},
    "AL": {"name": "ALABAMA", "color": (139, 0, 0), "accent": (255, 255, 255)},
    "AR": {"name": "ARKANSAS", "color": (0, 0, 128), "accent": (255, 255, 255)},
    "VA": {"name": "VIRGINIA", "color": (0, 50, 100), "accent": (255, 200, 50)},
    "SC": {"name": "SOUTH CAROLINA", "color": (0, 60, 120), "accent": (255, 255, 255)},
}

# 5 test drivers matching the roster
DRIVERS = [
    {"name": "JAMES R MITCHELL",     "dob": "04/12/1978", "lic": "TN-88234591", "state": "TN", "exp": "04/12/2028", "sex": "M", "ht": "5-11", "wt": "190", "eyes": "BRN", "endorsements": "T, N", "restrictions": "NONE"},
    {"name": "ROBERT A WILLIAMS",    "dob": "09/22/1985", "lic": "TN-77123488", "state": "TN", "exp": "09/22/2028", "sex": "M", "ht": "6-01", "wt": "210", "eyes": "BLU", "endorsements": "T, N", "restrictions": "NONE"},
    {"name": "DAVID L THOMPSON",     "dob": "01/30/1990", "lic": "AL-55987234", "state": "AL", "exp": "01/30/2028", "sex": "M", "ht": "5-10", "wt": "185", "eyes": "GRN", "endorsements": "T", "restrictions": "NONE"},
    {"name": "MICHAEL J GARCIA",     "dob": "07/15/1982", "lic": "AR-44321876", "state": "AR", "exp": "07/15/2027", "sex": "M", "ht": "5-09", "wt": "175", "eyes": "BRN", "endorsements": "T, N, H", "restrictions": "NONE"},
    {"name": "KEVIN D BROWN",        "dob": "11/05/1988", "lic": "TN-99876543", "state": "TN", "exp": "11/05/2028", "sex": "M", "ht": "6-02", "wt": "225", "eyes": "BRN", "endorsements": "T", "restrictions": "NONE"},
]


def _get_font(size, bold=False):
    paths = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSMono.ttf",
        "/Library/Fonts/Arial.ttf",
    ]
    for fp in paths:
        if os.path.exists(fp):
            try:
                return ImageFont.truetype(fp, size)
            except Exception:
                continue
    return ImageFont.load_default()


def create_cdl_card(driver: dict, index: int) -> str:
    img = Image.new("RGB", (CARD_W, CARD_H), WHITE)
    draw = ImageDraw.Draw(img)
    state = driver["state"]
    si = STATE_INFO.get(state, STATE_INFO["TN"])

    # Header
    draw.rectangle([0, 0, CARD_W, 55], fill=si["color"])
    draw.text((15, 5), f"STATE OF {si['name']}", fill=WHITE, font=_get_font(22, True))
    draw.text((15, 33), "COMMERCIAL DRIVER LICENSE - CLASS A", fill=si["accent"], font=_get_font(14, True))

    # CDL badge
    draw.rectangle([CARD_W - 80, 5, CARD_W - 10, 50], fill=GOLD, outline=DARK_BLUE)
    draw.text((CARD_W - 68, 12), "CDL", fill=DARK_BLUE, font=_get_font(18, True))
    draw.text((CARD_W - 72, 34), "CLASS A", fill=DARK_BLUE, font=_get_font(10, True))

    # Photo placeholder
    draw.rectangle([15, 65, 135, 215], fill=LIGHT_GRAY, outline=MEDIUM_GRAY, width=2)
    draw.text((40, 125), "PHOTO", fill=MEDIUM_GRAY, font=_get_font(10))
    draw.text((55, 140), "ID", fill=MEDIUM_GRAY, font=_get_font(10))

    # Info fields
    ix = 155
    fl, fv, fs = _get_font(9), _get_font(13, True), _get_font(10)
    y = 65

    draw.text((ix, y), "DL", fill=RED, font=fl)
    draw.text((ix + 25, y - 2), driver["lic"], fill=BLACK, font=fv)
    y += 22
    draw.text((ix, y), "CLASS", fill=RED, font=fl)
    draw.text((ix + 45, y - 2), "A", fill=BLACK, font=fv)
    draw.text((ix + 120, y), "ENDORSEMENTS", fill=RED, font=fl)
    draw.text((ix + 220, y - 2), driver["endorsements"], fill=BLACK, font=fv)
    y += 22
    draw.text((ix, y), "EXP", fill=RED, font=fl)
    draw.text((ix + 35, y - 2), driver["exp"], fill=BLACK, font=fv)
    draw.text((ix + 190, y), "RESTRICTIONS", fill=RED, font=fl)
    draw.text((ix + 290, y - 2), driver["restrictions"], fill=BLACK, font=fs)
    y += 28
    draw.line([(ix, y), (CARD_W - 15, y)], fill=MEDIUM_GRAY, width=1)
    y += 8
    draw.text((ix, y), "NAME", fill=RED, font=fl)
    draw.text((ix + 50, y - 3), driver["name"], fill=BLACK, font=_get_font(15, True))
    y += 24
    draw.text((ix, y), "DOB", fill=RED, font=fl)
    draw.text((ix + 35, y - 2), driver["dob"], fill=BLACK, font=fv)
    draw.text((ix + 190, y), "SEX", fill=RED, font=fl)
    draw.text((ix + 220, y - 2), driver["sex"], fill=BLACK, font=fv)
    y += 22
    draw.text((ix, y), "HT", fill=RED, font=fl)
    draw.text((ix + 25, y - 2), driver["ht"], fill=BLACK, font=fs)
    draw.text((ix + 85, y), "WT", fill=RED, font=fl)
    draw.text((ix + 110, y - 2), f'{driver["wt"]} lbs', fill=BLACK, font=fs)
    draw.text((ix + 190, y), "EYES", fill=RED, font=fl)
    draw.text((ix + 225, y - 2), driver["eyes"], fill=BLACK, font=fs)
    y += 22
    draw.text((ix, y), "ISS", fill=RED, font=fl)
    draw.text((ix + 30, y - 2), "06/15/2024", fill=BLACK, font=fs)
    draw.text((ix + 190, y), "STATUS", fill=RED, font=fl)
    draw.text((ix + 240, y - 2), "VALID", fill=(0, 120, 0), font=_get_font(11, True))

    # Bottom bar
    draw.rectangle([0, CARD_H - 50, CARD_W, CARD_H], fill=si["color"])
    draw.text((15, CARD_H - 45), f"DEPARTMENT OF MOTOR VEHICLES — {si['name']}", fill=WHITE, font=_get_font(9))
    draw.text((15, CARD_H - 28), "THIS LICENSE IS VALID FOR COMMERCIAL MOTOR VEHICLE OPERATION", fill=si["accent"], font=_get_font(9))
    draw.text((15, CARD_H - 14), f"DRIVER #{index+1:02d} | ISSUED: 06/15/2024 | NOT VALID WITHOUT PHOTO", fill=LIGHT_BLUE, font=_get_font(8))

    draw.rectangle([0, 0, CARD_W - 1, CARD_H - 1], outline=si["color"], width=3)

    fname = f"CDL_{driver['state']}_{driver['lic'].replace('-', '_')}_{driver['name'].split()[0]}_{driver['name'].split()[-1]}.png"
    path = os.path.join(OUT_DIR, fname)
    img.save(path, "PNG", quality=95)
    return path


def create_combined_pdf():
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas as pdf_canvas

    path = os.path.join(os.path.dirname(__file__), "perfect-submission",
                        "Heartland_Express_Driver_Licenses.pdf")
    c = pdf_canvas.Canvas(path, pagesize=letter)
    page_w, page_h = letter

    card_paths = []
    for i, driver in enumerate(DRIVERS):
        card_path = create_cdl_card(driver, i)
        card_paths.append(card_path)
        print(f"  ✅ Card {i+1}: {driver['name']} ({driver['lic']})")

    # Layout: 2 cols x 3 rows per page
    card_draw_w, card_draw_h = 3.2 * inch, 2.0 * inch
    margin_x, margin_y = 0.4 * inch, 0.5 * inch
    gap_x, gap_y = 0.3 * inch, 0.3 * inch
    cards_per_page = 6

    for page_idx in range(0, len(card_paths), cards_per_page):
        if page_idx > 0:
            c.showPage()
        page_cards = card_paths[page_idx:page_idx + cards_per_page]
        c.setFont("Helvetica-Bold", 14)
        c.setFillColorRGB(0.12, 0.23, 0.54)
        c.drawString(margin_x, page_h - 0.4 * inch,
                     "HEARTLAND EXPRESS TRUCKING LLC — DRIVER CDL COPIES")
        c.setFont("Helvetica", 9)
        c.setFillColorRGB(0.4, 0.4, 0.4)
        c.drawString(margin_x, page_h - 0.6 * inch,
                     f"Page {page_idx // cards_per_page + 1} | {len(DRIVERS)} Total Drivers | All CDLs Valid & Current")

        for i, card_path in enumerate(page_cards):
            col, row = i % 2, i // 2
            x = margin_x + col * (card_draw_w + gap_x)
            y = page_h - 0.8 * inch - (row + 1) * (card_draw_h + gap_y)
            c.drawImage(card_path, x, y, width=card_draw_w, height=card_draw_h)

    c.save()
    print(f"\n📄 Combined PDF: {path}")
    return path


if __name__ == "__main__":
    print("Generating CDL card images for 5 drivers...\n")
    combined_path = create_combined_pdf()
    print(f"\n📁 Individual cards: {OUT_DIR}/")
    print(f"📄 Combined PDF: {combined_path}")
    print(f"\n✅ Generated {len(DRIVERS)} CDL cards")
