import os
import json
import requests
from datetime import datetime, timezone

# ===========================
# Config
# ===========================
DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]

USAGE_FILE = "usage.json"
PREV_FILE = "usage_prev.json"
MONTHLY_FILE = "monthly_totals.json"
MESSAGE_FILE = "message_id.txt"

# Railway pricing
CPU_PRICE_PER_SEC = 0.00000772
MEMORY_PRICE_PER_GB_SEC = 0.00000386
VOLUME_PRICE_PER_GB_SEC = 0.00000006
NETWORK_PRICE_PER_GB = 0.05

now = datetime.now(timezone.utc)
month_key = now.strftime("%Y-%m")

# ===========================
# Load usage
# ===========================
with open(USAGE_FILE) as f:
    usage = json.load(f)

# ===========================
# Load previous snapshot
# ===========================
if os.path.exists(PREV_FILE):
    prev = json.load(open(PREV_FILE))
else:
    prev = {
        "cpuSeconds": 0,
        "memoryMBSeconds": 0,
        "networkEgressMB": 0,
        "volumeGBSeconds": 0
    }

# ===========================
# Delta calculation
# ===========================
delta_cpu = usage["cpuSeconds"] - prev["cpuSeconds"]
delta_mem_mb_sec = usage["memoryMBSeconds"] - prev["memoryMBSeconds"]
delta_net_mb = usage["networkEgressMB"] - prev["networkEgressMB"]
delta_vol_gb_sec = usage.get("volumeGBSeconds", 0) - prev.get("volumeGBSeconds", 0)

delta_mem_gb_sec = delta_mem_mb_sec / 1024
delta_net_gb = delta_net_mb / 1024

# ===========================
# Cost calculation
# ===========================
cpu_cost = delta_cpu * CPU_PRICE_PER_SEC
mem_cost = delta_mem_gb_sec * MEMORY_PRICE_PER_GB_SEC
vol_cost = delta_vol_gb_sec * VOLUME_PRICE_PER_GB_SEC
net_cost = delta_net_gb * NETWORK_PRICE_PER_GB

delta_total = cpu_cost + mem_cost + vol_cost + net_cost

# ===========================
# Monthly totals
# ===========================
def safe_load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return default

monthly = safe_load_json(MONTHLY_FILE, {})

if month_key not in monthly:
    monthly[month_key] = 0.0

monthly[month_key] += delta_total

# ===========================
# Discord embed
# ===========================
embed = {
    "title": "📊 Railway Usage Report",
    "color": 0x00C853,
    "fields": [
        {"name": "💻 CPU", "value": f"${cpu_cost:.4f}", "inline": True},
        {"name": "🧠 Memory", "value": f"${mem_cost:.4f}", "inline": True},
        {"name": "📦 Volumes", "value": f"${vol_cost:.4f}", "inline": True},
        {"name": "🌐 Network", "value": f"${net_cost:.4f}", "inline": True},
        {
            "name": "🗓️ This Period",
            "value": f"**${monthly[month_key]:.2f}**",
            "inline": False
        }
    ],
    "footer": {
        "text": f"Updated {now.strftime('%Y-%m-%d %H:%M UTC')} • Incremental + monthly total"
    }
}

payload = {"embeds": [embed]}

# ===========================
# Send or edit message
# ===========================
if os.path.exists(MESSAGE_FILE):
    msg_id = open(MESSAGE_FILE).read().strip()
    url = f"{DISCORD_WEBHOOK}/messages/{msg_id}"
    r = requests.patch(url, json=payload)
else:
    r = requests.post(DISCORD_WEBHOOK, json=payload)
    msg_id = r.json()["id"]
    open(MESSAGE_FILE, "w").write(msg_id)

r.raise_for_status()

# ===========================
# Save state
# ===========================
json.dump(usage, open(PREV_FILE, "w"))
json.dump(monthly, open(MONTHLY_FILE, "w"))

print("✅ Usage updated successfully")
