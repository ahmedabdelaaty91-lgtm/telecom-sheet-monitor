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

ALL_MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

def normalize_status(s):
    if not s:
        return ""
    s_clean = s.strip().lower()
    if s_clean == "collected":
        return "collected"
    if s_clean == "accepted":
        return "Accepted"
    if s_clean == "accepted technical":
        return "Accepted Technical"
    if "impelementation" in s_clean or "implementation" in s_clean:
        return "under impelementation"
    if "waiting" in s_clean:
        return "waiting ACC F.B"
    return s.strip()

def normalize_month(m):
    if not m:
        return ""
    m_clean = m.strip().lower()
    for name in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']:
        if m_clean.startswith(name):
            return name.capitalize()
    return MONTH_MAP.get(m_clean, m.strip())

def fetch_sheet_csv(url=DEFAULT_SHEET_URL):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp:
        content = resp.read().decode('utf-8', errors='ignore')
    return content

def compute_pivot_data(csv_text_or_path):
    if os
