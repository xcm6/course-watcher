import os
import json
import sys
import requests

URL = os.environ.get("WATCH_URL", "").strip()
if not URL:
    print("ERROR: Missing WATCH_URL")
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

def notify(msg: str):
    token = os.environ.get("PUSHOVER_APP_TOKEN", "").strip()
    user = os.environ.get("PUSHOVER_USER_KEY", "").strip()
    if not token or not user:
        print("Pushover not configured")
        return

    r = requests.post(
        "https://api.pushover.net/1/messages.json",
        data={
            "token": token,
            "user": user,
            "message": msg
        },
        timeout=15
    )
    r.raise_for_status()

def main():
    state = load_state()
    ran_before = state.get("ran_before", False)

    if not ran_before:
        # 第一次运行：不推送，只打标记
        print("TEST MODE: first run, no notification.")
        state["ran_before"] = True
    else:
        # 测试模式：每次都推送，确保你能收到
        notify(f"✅ TEST 推送成功：GitHub Actions → Pushover 正常工作\n{URL}")
        print("TEST MODE: notification sent.")

    save_state(state)

if __name__ == "__main__":
    main()
