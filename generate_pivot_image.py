import os
import csv
import io
import urllib.request
from collections import defaultdict
from PIL import Image, ImageDraw, ImageFont

DEFAULT_SHEET_URL = "https://docs.google.com/spreadsheets/d/1nv8eAlRiUQAqYy5cL5V_LhQl0Ht6tD3caFKUZoVQrOY/export?format=csv&gid=0"

MONTH_MAP = {
    'january/26': 'Jan', 'january': 'Jan', 'jan': 'Jan',
    'february/26': 'Feb', 'febraury/26': 'Feb', 'february': 'Feb', 'feb': 'Feb',
    'march/26': 'Mar', 'march': 'Mar', 'mar': 'Mar',
    'april/26': 'Apr', 'april': 'Apr', 'apr': 'Apr',
    'may/26': 'May', 'may': 'May',
    'june/26': 'Jun', 'june': 'Jun', 'jun': 'Jun',
    'july/26': 'Jul', 'july': 'Jul', 'jul': 'Jul',
    'august/26': 'Aug', 'august': 'Aug', 'aug': 'Aug',
    'september/26': 'Sep', 'september': 'Sep', 'sep': 'Sep',
    'october/26': 'Oct', 'october': 'Oct', 'oct': 'Oct',
    'november/26': 'Nov', 'november': 'Nov', 'nov': 'Nov',
    'december/26': 'Dec', 'december': 'Dec', 'dec': 'Dec'
}

STATUS_COLS = [
    'collected',
    'Accepted',
    'Accepted Technical',
    'under impelementation',
    'waiting ACC F.B'
]

ALL_MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep']

def fetch_sheet_csv(url=DEFAULT_SHEET_URL):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp:
        content = resp.read().decode('utf-8', errors='ignore')
    return content

def compute_pivot_data(csv_text_or_path):
    if os.path.exists(csv_text_or_path):
        with open(csv_text_or_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
    else:
        reader = csv.DictReader(io.StringIO(csv_text_or_path))
        rows = list(reader)

    pivot = defaultdict(lambda: defaultdict(float))
    seen_months = []

    for r in rows:
        raw_m = r.get('Executed Month', '').strip().lower()
        m = MONTH_MAP.get(raw_m, raw_m)
        if not m:
            continue
        if m not in seen_months and m in ALL_MONTHS:
            seen_months.append(m)
        status = r.get('Last acceptance status', '').strip()
        val_str = r.get('Signed Value', '0').replace(',', '').strip()
        try:
            val = float(val_str) if val_str else 0.0
        except:
            val = 0.0
        pivot[m][status] += val

    months = [m for m in ALL_MONTHS if m in seen_months or pivot[m]]
    if not months:
        months = ALL_MONTHS

    col_totals = defaultdict(float)
    row_totals = defaultdict(float)
    grand_total = 0.0

    for m in months:
        r_sum = 0.0
        for c in STATUS_COLS:
            v = pivot[m].get(c, 0.0)
            col_totals[c] += v
            r_sum += v
        row_totals[m] = r_sum
        grand_total += r_sum

    return {
        'months': months,
        'cols': STATUS_COLS,
        'pivot': pivot,
        'row_totals': row_totals,
        'col_totals': col_totals,
        'grand_total': grand_total
    }

def draw_plus_icon(draw, x, y, size=11):
    # Draw small square with + inside
    draw.rectangle([x, y, x + size, y + size], outline=(200, 200, 200), fill=(240, 240, 240))
    # horizontal bar of +
    mid_y = y + size // 2
    mid_x = x + size // 2
    draw.line([x + 2, mid_y, x + size - 2, mid_y], fill=(50, 50, 50), width=1)
    # vertical bar of +
    draw.line([mid_x, y + 2, mid_x, y + size - 2], fill=(50, 50, 50), width=1)

def render_pivot_image(data, output_path="pivot_table.png", scale=2):
    # Base layout specs (at scale 1x):
    # Col x positions: 0, 136, 228, 320, 442, 590, 692, 784
    col_widths = [136, 92, 92, 122, 148, 102, 92]
    total_w = sum(col_widths) # 784
    
    header_h = 44
    row_h = 20
    num_rows = len(data['months'])
    # header_h + num_rows * row_h + grand_total_row_h + pct_row_h
    total_h = header_h + (num_rows + 2) * row_h # 44 + 11*20 = 264

    # We render at scale factor for crisp rendering then return
    W = total_w * scale
    H = total_h * scale

    img = Image.new("RGBA", (W, H), (255, 255, 255, 255))
    draw = ImageDraw.Draw(img)

    # Fonts
    local_fonts_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
    candidate_bolds = [
        os.path.join(local_fonts_dir, "arialbd.ttf"),
        r"C:\Windows\Fonts\arialbd.ttf",
        r"C:\Windows\Fonts\calibrib.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    ]
    font_path_bold = None
    for p in candidate_bolds:
        if os.path.exists(p):
            font_path_bold = p
            break

    candidate_regs = [
        os.path.join(local_fonts_dir, "arial.ttf"),
        r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\calibri.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    ]
    font_path_reg = None
    for p in candidate_regs:
        if os.path.exists(p):
            font_path_reg = p
            break

    if font_path_bold:
        font_header = ImageFont.truetype(font_path_bold, int(13 * scale))
        font_header_sub = ImageFont.truetype(font_path_bold, int(12 * scale))
        font_data = ImageFont.truetype(font_path_bold, int(11 * scale))
        font_pct = ImageFont.truetype(font_path_bold, int(12 * scale))
    else:
        font_header = ImageFont.load_default()
        font_header_sub = ImageFont.load_default()
        font_data = ImageFont.load_default()
        font_pct = ImageFont.load_default()

    # Colors
    C_HEADER_BG = (64, 64, 64, 255)
    C_ROW_LABEL_BG = (64, 64, 64, 255)
    C_CELL_BLUE_BG = (47, 117, 181, 255)
    C_GRAND_TOTAL_BG = (64, 64, 64, 255)
    C_PCT_BG = (255, 255, 255, 255)
    C_GRID = (0, 0, 0, 255)
    C_WHITE = (255, 255, 255, 255)
    C_BLACK = (0, 0, 0, 255)

    col_xs = [0]
    for w in col_widths:
        col_xs.append(col_xs[-1] + w)

    # 1. Fill Header Row (Row 0)
    for c_idx in range(len(col_widths)):
        x1 = col_xs[c_idx] * scale
        x2 = col_xs[c_idx + 1] * scale
        y1 = 0
        y2 = header_h * scale
        draw.rectangle([x1, y1, x2, y2], fill=C_HEADER_BG)

    # Header texts
    headers = [
        "executed month",
        "collected",
        "Accepted",
        "Accepted Technical",
        "under impelementation",
        "waiting ACC F.B",
        "Grand Total"
    ]

    for c_idx, h_text in enumerate(headers):
        x1 = col_xs[c_idx] * scale
        x2 = col_xs[c_idx + 1] * scale
        cell_w = x2 - x1
        cell_h = header_h * scale

        f = font_header
        # text bounding box
        bbox = f.getbbox(h_text)
        t_w = bbox[2] - bbox[0]
        t_h = bbox[3] - bbox[1]

        if c_idx == 0:
            # left align
            tx = x1 + int(8 * scale)
            ty = (cell_h - t_h) // 2
            draw.text((tx, ty), h_text, font=f, fill=C_WHITE)
            # Filter icon on the right of header 0
            icon_x = x2 - int(16 * scale)
            icon_y = (cell_h - int(12 * scale)) // 2
            draw.rectangle([icon_x, icon_y, icon_x + int(12 * scale), icon_y + int(12 * scale)], fill=(230, 230, 230))
            draw.line([icon_x + int(2 * scale), icon_y + int(6 * scale), icon_x + int(6 * scale), icon_y + int(10 * scale)], fill=C_BLACK, width=max(1, scale))
            draw.line([icon_x + int(6 * scale), icon_y + int(10 * scale), icon_x + int(10 * scale), icon_y + int(6 * scale)], fill=C_BLACK, width=max(1, scale))
        else:
            # Centered or right aligned
            # Headers in reference image are centered/wrapped
            tx = x1 + (cell_w - t_w) // 2
            ty = (cell_h - t_h) // 2
            draw.text((tx, ty), h_text, font=f, fill=C_WHITE)

    # 2. Draw Month Rows
    curr_y = header_h
    for m_idx, m in enumerate(data['months']):
        y1 = curr_y * scale
        y2 = (curr_y + row_h) * scale
        cell_h = y2 - y1

        # Month label cell
        x1 = col_xs[0] * scale
        x2 = col_xs[1] * scale
        draw.rectangle([x1, y1, x2, y2], fill=C_ROW_LABEL_BG)

        # Draw [+] icon
        icon_size = int(10 * scale)
        icon_x = x1 + int(24 * scale)
        icon_y = y1 + (cell_h - icon_size) // 2
        draw_plus_icon(draw, icon_x, icon_y, size=icon_size)

        # Draw month name
        m_name = m
        bbox = font_data.getbbox(m_name)
        draw.text((icon_x + icon_size + int(6 * scale), y1 + (cell_h - (bbox[3] - bbox[1])) // 2 - int(2 * scale)), m_name, font=font_data, fill=C_WHITE)

        # Data cells
        for c_idx, c_name in enumerate(data['cols']):
            cx1 = col_xs[c_idx + 1] * scale
            cx2 = col_xs[c_idx + 2] * scale
            draw.rectangle([cx1, y1, cx2, y2], fill=C_CELL_BLUE_BG)

            val = data['pivot'][m].get(c_name, 0.0)
            if val > 0:
                val_str = f"{val:,.2f}"
                bbox = font_data.getbbox(val_str)
                t_w = bbox[2] - bbox[0]
                tx = cx2 - t_w - int(8 * scale)
                ty = y1 + (cell_h - (bbox[3] - bbox[1])) // 2 - int(2 * scale)
                draw.text((tx, ty), val_str, font=font_data, fill=C_WHITE)

        # Row Grand Total
        gt_x1 = col_xs[-2] * scale
        gt_x2 = col_xs[-1] * scale
        draw.rectangle([gt_x1, y1, gt_x2, y2], fill=C_CELL_BLUE_BG)
        r_tot = data['row_totals'][m]
        if r_tot > 0:
            val_str = f"{r_tot:,.2f}"
            bbox = font_data.getbbox(val_str)
            t_w = bbox[2] - bbox[0]
            tx = gt_x2 - t_w - int(8 * scale)
            ty = y1 + (cell_h - (bbox[3] - bbox[1])) // 2 - int(2 * scale)
            draw.text((tx, ty), val_str, font=font_data, fill=C_WHITE)

        curr_y += row_h

    # 3. Grand Total Row
    y1 = curr_y * scale
    y2 = (curr_y + row_h) * scale
    cell_h = y2 - y1

    # Col 0: "Grand Total"
    x1 = col_xs[0] * scale
    x2 = col_xs[1] * scale
    draw.rectangle([x1, y1, x2, y2], fill=C_GRAND_TOTAL_BG)
    gt_label = "Grand Total"
    bbox = font_data.getbbox(gt_label)
    tx = x1 + (x2 - x1 - (bbox[2] - bbox[0])) // 2
    ty = y1 + (cell_h - (bbox[3] - bbox[1])) // 2 - int(2 * scale)
    draw.text((tx, ty), gt_label, font=font_data, fill=C_WHITE)

    # Data columns totals
    for c_idx, c_name in enumerate(data['cols']):
        cx1 = col_xs[c_idx + 1] * scale
        cx2 = col_xs[c_idx + 2] * scale
        draw.rectangle([cx1, y1, cx2, y2], fill=C_GRAND_TOTAL_BG)

        val = data['col_totals'][c_name]
        if val > 0:
            val_str = f"{val:,.2f}"
            bbox = font_data.getbbox(val_str)
            t_w = bbox[2] - bbox[0]
            tx = cx2 - t_w - int(8 * scale)
            ty = y1 + (cell_h - (bbox[3] - bbox[1])) // 2 - int(2 * scale)
            draw.text((tx, ty), val_str, font=font_data, fill=C_WHITE)

    # Grand total of grand total
    gt_x1 = col_xs[-2] * scale
    gt_x2 = col_xs[-1] * scale
    draw.rectangle([gt_x1, y1, gt_x2, y2], fill=C_GRAND_TOTAL_BG)
    val = data['grand_total']
    val_str = f"{val:,.2f}"
    bbox = font_data.getbbox(val_str)
    t_w = bbox[2] - bbox[0]
    tx = gt_x2 - t_w - int(8 * scale)
    ty = y1 + (cell_h - (bbox[3] - bbox[1])) // 2 - int(2 * scale)
    draw.text((tx, ty), val_str, font=font_data, fill=C_WHITE)

    curr_y += row_h

    # 4. Percentage Row
    y1 = curr_y * scale
    y2 = (curr_y + row_h) * scale
    cell_h = y2 - y1

    # Col 0: White
    x1 = col_xs[0] * scale
    x2 = col_xs[1] * scale
    draw.rectangle([x1, y1, x2, y2], fill=C_PCT_BG)

    # Data columns percentages
    for c_idx, c_name in enumerate(data['cols']):
        cx1 = col_xs[c_idx + 1] * scale
        cx2 = col_xs[c_idx + 2] * scale
        draw.rectangle([cx1, y1, cx2, y2], fill=C_PCT_BG)

        val = data['col_totals'][c_name]
        pct = round((val / data['grand_total'] * 100)) if data['grand_total'] else 0
        pct_str = f"{pct}%"
        bbox = font_pct.getbbox(pct_str)
        t_w = bbox[2] - bbox[0]
        tx = cx1 + (cx2 - cx1 - t_w) // 2
        ty = y1 + (cell_h - (bbox[3] - bbox[1])) // 2 - int(2 * scale)
        draw.text((tx, ty), pct_str, font=font_pct, fill=C_BLACK)

    # Col Grand Total: White
    gt_x1 = col_xs[-2] * scale
    gt_x2 = col_xs[-1] * scale
    draw.rectangle([gt_x1, y1, gt_x2, y2], fill=C_PCT_BG)

    curr_y += row_h

    # 5. Grid Lines (Black lines)
    # Vertical grid lines
    line_w = max(1, scale)
    for cx in col_xs:
        draw.line([cx * scale, 0, cx * scale, H], fill=C_GRID, width=line_w)

    # Horizontal grid lines
    h_ys = [0, header_h]
    for r in range(num_rows + 2):
        h_ys.append(header_h + (r + 1) * row_h)
    
    for hy in h_ys:
        draw.line([0, hy * scale, W, hy * scale], fill=C_GRID, width=line_w)

    # Outer border
    draw.rectangle([0, 0, W - 1, H - 1], outline=C_GRID, width=line_w)

    # Save image
    img.save(output_path, "PNG")
    print(f"Pivot table image saved to: {output_path}")
    return output_path

if __name__ == "__main__":
    import sys
    src = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_SHEET_URL
    if src.startswith("http"):
        print(f"Fetching from {src}...")
        csv_data = fetch_sheet_csv(src)
    else:
        csv_data = src
    data = compute_pivot_data(csv_data)
    out_file = render_pivot_image(data, "pivot_table.png")
