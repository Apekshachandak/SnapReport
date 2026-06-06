"""
pdf_generator.py — ReportLab canvas-based PDF report generator for SnapReport.
Uses direct canvas drawing for pixel-precise layout control.
"""

import os
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.utils import simpleSplit

# ── Palette ──────────────────────────────────────────────────────
NAVY      = HexColor("#1B3F72")
NAVY_DARK = HexColor("#122D55")
GOLD      = HexColor("#D4A017")
LIGHT_BG  = HexColor("#EEF2F9")
GREY_TXT  = HexColor("#6B7280")
DARK_TXT  = HexColor("#1A1A2E")
ALT_ROW   = HexColor("#F3F4F6")
BORDER    = HexColor("#D1D5DB")
GREEN     = HexColor("#16A34A")

PAGE_W, PAGE_H = A4   # 595.27 x 841.89 pt
LM = 36               # left margin
RM = 36               # right margin
USABLE = PAGE_W - LM - RM


# ── Helpers ───────────────────────────────────────────────────────

def _fmt_price(value: int) -> str:
    if not value:
        return "N/A"
    if value >= 1_000_000:
        return f"${value / 1_000_000:.2f}M"
    return f"${value:,}"


def _draw_rounded_rect(c, x, y, w, h, r=6, fill_color=None, stroke_color=None, stroke_width=0.5):
    if fill_color:
        c.setFillColor(fill_color)
    if stroke_color:
        c.setStrokeColor(stroke_color)
        c.setLineWidth(stroke_width)
    else:
        c.setStrokeColor(HexColor("#CCCCCC"))
        c.setLineWidth(0.3)
    c.roundRect(x, y, w, h, r, fill=1 if fill_color else 0, stroke=1 if stroke_color else 0)


def _draw_text(c, text, x, y, font="Helvetica", size=10, color=DARK_TXT, align="left"):
    c.setFont(font, size)
    c.setFillColor(color)
    if align == "right":
        c.drawRightString(x, y, text)
    elif align == "center":
        c.drawCentredString(x, y, text)
    else:
        c.drawString(x, y, text)


def _wrapped_text(c, text, x, y, max_width, font="Helvetica", size=10, color=DARK_TXT, line_height=14):
    """Draw wrapped text, returns final y position."""
    c.setFont(font, size)
    c.setFillColor(color)
    lines = simpleSplit(text, font, size, max_width)
    for line in lines:
        c.drawString(x, y, line)
        y -= line_height
    return y


# ── Section Drawers ───────────────────────────────────────────────

def _draw_header(c, page_w, page_h):
    """Navy header bar with gold accent line."""
    bar_h = 54
    top = page_h - bar_h
    c.setFillColor(NAVY)
    c.rect(0, top, page_w, bar_h, fill=1, stroke=0)

    # SNAPHOMZ brand
    _draw_text(c, "SNAPHOMZ", LM, top + 20, "Helvetica-Bold", 20, white)

    # Right subtitle
    subtitle = "Market Intelligence Report"
    c.setFont("Helvetica-Oblique", 10)
    c.setFillColor(HexColor("#B8CCE8"))
    sw = c.stringWidth(subtitle, "Helvetica-Oblique", 10)
    c.drawString(page_w - RM - sw, top + 21, subtitle)

    # Gold accent line
    c.setFillColor(GOLD)
    c.rect(0, top - 3, page_w, 3, fill=1, stroke=0)

    return top - 3  # return bottom of header area


def _draw_title_section(c, zip_code, report_date, y_top):
    """ZIP title, subtitle, horizontal rule."""
    y = y_top - 22
    _draw_text(c, f"ZIP {zip_code}", LM, y, "Helvetica-Bold", 30, NAVY)
    y -= 16
    _draw_text(c, f"Neighbourhood Market Report  ·  {report_date}", LM, y, "Helvetica-Oblique", 10, GREY_TXT)
    y -= 10
    c.setStrokeColor(NAVY)
    c.setLineWidth(0.8)
    c.line(LM, y, PAGE_W - RM, y)
    return y - 6


def _draw_agent_card(c, agent: dict, y_top):
    """Agent info card — shown only if agent data provided."""
    if not agent or not agent.get("name"):
        return y_top

    card_h = 50
    y = y_top - card_h - 4
    _draw_rounded_rect(c, LM, y, USABLE, card_h, r=6,
                       fill_color=LIGHT_BG, stroke_color=BORDER, stroke_width=0.5)

    # Left navy accent
    c.setFillColor(NAVY)
    c.rect(LM, y, 4, card_h, fill=1, stroke=0)

    # Agent info
    cx = LM + 16
    _draw_text(c, "PREPARED BY", cx, y + card_h - 14, "Helvetica-Bold", 7, GREY_TXT)
    _draw_text(c, agent.get("name", ""), cx, y + card_h - 26, "Helvetica-Bold", 12, NAVY)
    contact_parts = []
    if agent.get("phone"):
        contact_parts.append(agent["phone"])
    if agent.get("email"):
        contact_parts.append(agent["email"])
    if agent.get("company"):
        contact_parts.append(agent["company"])
    if contact_parts:
        _draw_text(c, "  |  ".join(contact_parts), cx, y + card_h - 40, "Helvetica", 9, GREY_TXT)

    return y - 8


def _draw_stats_grid(c, stats, y_top):
    """2 rows × 3 cols of stat cards."""
    cols = 3
    gap = 10
    card_h = 70
    card_w = (USABLE - gap * (cols - 1)) / cols

    for i, stat in enumerate(stats[:6]):
        col = i % cols
        row = i // cols
        x = LM + col * (card_w + gap)
        y = y_top - (row + 1) * card_h - row * gap

        # Card background
        _draw_rounded_rect(c, x, y, card_w, card_h, r=5,
                           fill_color=LIGHT_BG, stroke_color=BORDER, stroke_width=0.4)
        # Navy left accent bar
        c.setFillColor(NAVY)
        c.rect(x, y, 4, card_h, fill=1, stroke=0)

        # Label
        _draw_text(c, stat["label"].upper(), x + 12, y + card_h - 16, "Helvetica-Bold", 7, GREY_TXT)
        # Value
        _draw_text(c, stat["value"], x + 12, y + card_h - 38, "Helvetica-Bold", 20, NAVY)
        # Sub
        _draw_text(c, stat["sub"], x + 12, y + 10, "Helvetica-Oblique", 7, GREY_TXT)

    rows = -(-len(stats[:6]) // cols)  # ceiling division
    return y_top - rows * card_h - (rows - 1) * gap - 10


def _draw_section_header(c, title, y):
    """Section title with left navy bar."""
    c.setFillColor(GOLD)
    c.rect(LM, y - 2, 3, 16, fill=1, stroke=0)
    _draw_text(c, title, LM + 10, y, "Helvetica-Bold", 13, NAVY)
    return y - 20


def _draw_narrative(c, narrative, y_top):
    """Market narrative block with light background."""
    max_w = USABLE - 24
    font, size, lh = "Helvetica", 10, 15

    c.setFont(font, size)
    lines = simpleSplit(narrative, font, size, max_w)
    block_h = len(lines) * lh + 20

    # Card background
    _draw_rounded_rect(c, LM, y_top - block_h, USABLE, block_h, r=5,
                       fill_color=HexColor("#F8FAFF"), stroke_color=BORDER, stroke_width=0.4)
    # Left navy border
    c.setFillColor(NAVY)
    c.rect(LM, y_top - block_h, 3, block_h, fill=1, stroke=0)

    # Text
    y = y_top - 14
    c.setFont(font, size)
    c.setFillColor(DARK_TXT)
    for line in lines:
        c.drawString(LM + 14, y, line)
        y -= lh

    return y_top - block_h - 10


def _draw_sales_table(c, sales, y_top):
    """Alternating-row recent sales table."""
    if not sales:
        return y_top

    col_widths = [USABLE * 0.55, USABLE * 0.22, USABLE * 0.23]
    row_h = 18
    header_h = 22

    # Header
    c.setFillColor(NAVY)
    c.rect(LM, y_top - header_h, USABLE, header_h, fill=1, stroke=0)
    headers = ["Address", "Sale Price", "Date"]
    x = LM
    for i, h in enumerate(headers):
        _draw_text(c, h, x + 8, y_top - 15, "Helvetica-Bold", 8, white)
        x += col_widths[i]

    # Data rows
    y = y_top - header_h
    for idx, sale in enumerate(sales[:8]):
        row_color = white if idx % 2 == 0 else ALT_ROW
        c.setFillColor(row_color)
        c.rect(LM, y - row_h, USABLE, row_h, fill=1, stroke=0)

        # Thin separator line
        c.setStrokeColor(BORDER)
        c.setLineWidth(0.3)
        c.line(LM, y - row_h, LM + USABLE, y - row_h)

        x = LM
        vals = [
            sale.get("address", "N/A")[:55],
            _fmt_price(sale.get("saleAmount", 0)),
            sale.get("saleDate", "N/A"),
        ]
        for i, val in enumerate(vals):
            _draw_text(c, val, x + 8, y - 13, "Helvetica", 8, DARK_TXT)
            x += col_widths[i]
        y -= row_h

    # Outer border
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.rect(LM, y, USABLE, y_top - y, fill=0, stroke=1)

    return y - 10


def _draw_footer(c, page_w, today_str):
    """Navy footer bar."""
    bar_h = 26
    c.setFillColor(NAVY)
    c.rect(0, 0, page_w, bar_h, fill=1, stroke=0)
    _draw_text(c, "Powered by Snaphomz  ·  snaphomz.com", LM, 9, "Helvetica", 7.5, white)
    right = f"Data: RealEstateAPI.com  ·  AI: Groq Llama 3.3  ·  Generated {today_str}"
    c.setFont("Helvetica", 7.5)
    c.setFillColor(white)
    rw = c.stringWidth(right, "Helvetica", 7.5)
    c.drawString(page_w - RM - rw, 9, right)


# ── Main Entry ────────────────────────────────────────────────────

def generate_pdf(market_data: dict, narrative: str,
                 output_dir: str = "./output",
                 agent: dict = None) -> str:
    """
    Generate a branded Snaphomz market report PDF.
    agent = {"name": str, "phone": str, "email": str, "company": str}
    Returns absolute path to saved PDF.
    """
    os.makedirs(output_dir, exist_ok=True)

    zip_code = market_data["zip"]
    today_str = datetime.today().strftime("%Y-%m-%d")
    filename = f"report_{zip_code}_{today_str}.pdf"
    output_path = os.path.join(output_dir, filename)

    c = canvas.Canvas(output_path, pagesize=A4)
    c.setTitle(f"SnapReport — ZIP {zip_code}")
    c.setAuthor("Snaphomz")

    # ── Draw page ────────────────────────────────────────────────
    y = _draw_header(c, PAGE_W, PAGE_H)
    y = _draw_title_section(c, zip_code, market_data["report_date"], y)

    # Agent card (optional)
    y = _draw_agent_card(c, agent or {}, y)

    # Stats
    total = (market_data["owner_occupied"] + market_data["vacant_count"]) or 1
    owner_pct = f"{round(market_data['owner_occupied'] / total * 100)}%"
    stats = [
        {"label": "Median List Price",  "value": _fmt_price(market_data["median_price"]),  "sub": "Current listing median"},
        {"label": "Days on Market",     "value": str(market_data["days_on_market"]),        "sub": "Avg. time to pending"},
        {"label": "Active Listings",    "value": str(market_data["active_listings"]),       "sub": "Currently on MLS"},
        {"label": "Pending Listings",   "value": str(market_data["pending_listings"]),      "sub": "Under contract"},
        {"label": "Sold (90 Days)",     "value": str(len(market_data["recent_sales"])),     "sub": "Closed transactions"},
        {"label": "Owner Occupied",     "value": owner_pct,                                 "sub": "Of tracked properties"},
    ]
    y = _draw_stats_grid(c, stats, y - 6)

    # Narrative
    y -= 10
    y = _draw_section_header(c, "Market Overview", y)
    y = _draw_narrative(c, narrative, y)

    # Sales table
    if market_data["recent_sales"]:
        y -= 4
        y = _draw_section_header(c, "Recent Sales — Last 90 Days", y)
        y = _draw_sales_table(c, market_data["recent_sales"], y)

    # Footer
    _draw_footer(c, PAGE_W, today_str)

    c.save()
    return output_path
