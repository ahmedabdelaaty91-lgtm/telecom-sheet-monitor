import os
import sys
import time
import json
import hashlib
import logging
import requests
from datetime import datetime
from generate_pivot_image import (
    DEFAULT_SHEET_URL,
    fetch_sheet_csv,
    compute_pivot_data,
    render_pivot_image
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")
HASH_FILE = os.path.join(BASE_DIR, "last_hash.txt")
IMAGE_FILE = os.path.join(BASE_DIR, "pivot_table.png")
LOG_FILE = os.path.join(BASE_DIR, "monitor.log")

# Logging configuration
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8")
    ]
)

DEFAULT_CONFIG = {
    "sheet_url": DEFAULT_SHEET_URL,
    "telegram_bot_token": "YOUR_BOT_TOKEN_HERE",
    "telegram_chat_id": "YOUR_CHAT_ID_HERE",
    "check_interval_seconds": 3600,
    "send_on_start": True
}

def load_config():
    cfg = DEFAULT_CONFIG.copy()
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except Exception as e:
            logging.error(f"Error reading {CONFIG_FILE}: {e}")
    else:
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_CONFIG, f, indent=4)
        except Exception:
            pass

    # Override from environment variables if set (useful for GitHub Actions)
    if os.environ.get("TELEGRAM_BOT_TOKEN"):
        cfg["telegram_bot_token"] = os.environ.get("TELEGRAM_BOT_TOKEN").strip()
    if os.environ.get("TELEGRAM_CHAT_ID"):
        cfg["telegram_chat_id"] = os.environ.get("TELEGRAM_CHAT_ID").strip()
    if os.environ.get("SHEET_URL"):
        cfg["sheet_url"] = os.environ.get("SHEET_URL").strip()

    return cfg

def get_last_hash():
    if os.path.exists(HASH_FILE):
        try:
            with open(HASH_FILE, "r", encoding="utf-8") as f:
                return f.read().strip()
        except Exception:
            return None
    return None

def save_last_hash(content_hash):
    try:
        with open(HASH_FILE, "w", encoding="utf-8") as f:
            f.write(content_hash)
    except Exception as e:
        logging.error(f"Failed to save hash: {e}")

def send_telegram_photo(bot_token, chat_id, photo_path, caption=""):
    url = f"https://api.telegram.org/bot{bot_token}/sendPhoto"
    logging.info(f"Sending updated photo to Telegram chat {chat_id}...")
    try:
        with open(photo_path, "rb") as f:
            files = {"photo": f}
            data = {"chat_id": chat_id, "caption": caption, "parse_mode": "Markdown"}
            resp = requests.post(url, data=data, files=files, timeout=30)
            res_json = resp.json()
            if res_json.get("ok"):
                logging.info("Photo sent successfully to Telegram!")
                return True
            else:
                logging.error(f"Telegram API error: {res_json}")
                return False
    except Exception as e:
        logging.error(f"Failed to send photo to Telegram: {e}")
        return False

def check_and_update(config, force_send=False):
    sheet_url = config.get("sheet_url", DEFAULT_SHEET_URL)
    bot_token = config.get("telegram_bot_token", "").strip()
    chat_id = str(config.get("telegram_chat_id", "")).strip()

    logging.info("Checking Google Sheet for updates...")
    try:
        csv_text = fetch_sheet_csv(sheet_url)
    except Exception as e:
        logging.error(f"Failed to fetch Google Sheet: {e}")
        return False

    current_hash = hashlib.md5(csv_text.encode('utf-8')).hexdigest()
    last_hash = get_last_hash()

    if not force_send and last_hash and current_hash == last_hash:
        logging.info("No changes detected in Google Sheet.")
        return False

    logging.info(f"Update detected! (Hash changed: {last_hash} -> {current_hash})")
    
    # Generate new pivot data & image
    data = compute_pivot_data(csv_text)
    img_path = IMAGE_FILE
    render_pivot_image(data, img_path)

    save_last_hash(current_hash)

    # If Telegram credentials are provided, send photo
    if bot_token and bot_token != "YOUR_BOT_TOKEN_HERE" and chat_id and chat_id != "YOUR_CHAT_ID_HERE":
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_val = f"{data['grand_total']:,.2f}"
        caption = (
            f"📊 *تحديث بيانات المشروعات*\n"
            f"🕒 التاريخ والوقت: `{now_str}`\n"
            f"💰 إجمالي القيمة: `{total_val}`\n"
            f"📈 نسبة التحصيل: `{(data['col_totals']['collected'] / data['grand_total'] * 100):.1f}%`"
        )
        send_telegram_photo(bot_token, chat_id, img_path, caption)
    else:
        logging.warning("Telegram Bot Token or Chat ID not configured. Updated image generated locally.")

    return True

def run_loop():
    logging.info("Starting Telecom Sheet Monitor loop...")
    first_run = True
    while True:
        config = load_config()
        interval = config.get("check_interval_seconds", 3600)
        send_on_start = config.get("send_on_start", True)

        try:
            force = first_run and send_on_start
            check_and_update(config, force_send=force)
        except Exception as e:
            logging.error(f"Unexpected error in check cycle: {e}")

        first_run = False
        logging.info(f"Sleeping for {interval} seconds ({interval / 60:.1f} minutes)...")
        time.sleep(interval)

if __name__ == "__main__":
    if "--once" in sys.argv:
        cfg = load_config()
        check_and_update(cfg, force_send=True)
    else:
        run_loop()
