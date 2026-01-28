import os
import re
import json
import sys
import requests
from bs4 import BeautifulSoup

URL = os.environ.get("WATCH_URL", "").strip()
if not URL:
    print("ERROR: Missing WATCH_URL secret/env var")
    sys.exit(2)

STATE_FILE = "state.json"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f)

def fetch_text():
    r = requests.get(
        URL,
        timeout=25,
        headers={"User-Agent": "Mozilla/5.0 (course-watcher; personal use)"}
    )
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    # 把页面文字压缩成单行，方便正则匹配
    return " ".join(soup.get_text(" ", strip=True).split())

def parse_seats_available(text: str):
    """
    匹配页面上的字段：Seats Available: Yes / No
    返回 "yes" / "no" / None
    """
    m = re.search(r"Seats\s+Available:\s*(Yes|No)", text, re.IGNORECASE)
    if not m:
        return None
    return m.group(1).lower()

def parse_status(text: str):
    """
    可选：匹配 Status: Open / Waitlist / Closed ...
    返回小写字符串或 None
    """
    m = re.search(r"Status:\s*([A-Za-z]+)", text, re.IGNORECASE)
    if not m:
        return None
    return m.group(1).lower()

def notify(msg: str):
    token = os.environ.get("PUSHOVER_APP_TOKEN", "").strip()
    user = os.environ.get("PUSHOVER_USER_KEY", "").strip()
    if not token or not user:
        print("WARN: Pushover not configured. Message:", msg)
        return

    resp = requests.post(
        "https://api.pushover.net/1/messages.json",
        data={"token": token, "user": user, "message": msg},
        timeout=15,
    )
    resp.raise_for_status()

def main():
    state = load_state()
    prev_seats = state.get("seats_available")  # "yes" / "no" / None

    text = fetch_text()
    seats = parse_seats_available(text)        # 当前 seats
    status = parse_status(text)                # 当前 status（可选）

    # 第一次运行：只记录，不提醒
    if prev_seats is None:
        print("First run. Recording current state only.")
    else:
        # 只在 no -> yes 的瞬间提醒一次
        if prev_seats == "no" and seats == "yes":
            notify(f"🚨 Seats Available: YES（有位置了）！状态={status}  快去注册：{URL}")

    # 保存当前状态
    state["seats_available"] = seats
    state["last_status"] = status
    save_state(state)

    print(f"OK seats={seats} prev={prev_seats} status={status}")

if __name__ == "__main__":
    main()
