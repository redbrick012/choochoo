import os
import json
import requests
from datetime import datetime, timezone

# =========================
# CONFIG
# =========================
DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]
USAGE_FILE = os.environ.get("USAGE_FILE", "usage.json")
PREV_FILE = os.environ.get("PREV_FILE", "usage_prev.json")
STATE_FILE = os.environ.get("STATE_FILE", "discord_state.json")

# =========================
# RAILWAY PRICING (USD)
# =========================
CPU_PRICE_PER_SEC = 0.00000772
MEMORY_PRICE_PER_GB_SEC = 0.00000386
VOLUME_PRICE_PER_GB_SEC = 0.00000006
NETWORK_PRICE_PER_GB = 0.05


# =========================
# SAFE JSON HELPERS
# =========================
def safe_load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, ValueError):
        return default


def safe_write_json(path, data):
    tmp = f"{path}.tmp"
    with open(tmp, "w") as f:
        json.dump(data, f)
    os.replace(tmp, path)


# =========================
# LOAD USAGE DATA
# =========================
usage = safe_load_json(USAGE_FILE, {})

prev = safe_load_json(PREV_FILE, {
    "cpuSeconds": 0,
    "memoryMBSeconds": 0,
    "networkEgressMB": 0,
    "volumeGBSeconds": 0
})

state = safe_load_json(STATE_FILE, {
    "message_id": None
})


# =========================
# NORMALISE KEYS
# =========================
def get(d, key):
    return d.get(key, 0)

cpu_now = get(usage, "cpuSeconds")
mem_now = get(usage, "memoryMBSeconds")
net_now = get(usage, "networkEgressMB")
vol_now = get(usage, "volumeGBSeconds")

cpu_prev = get(prev, "cpuSeconds")
mem_prev = get(prev, "memoryMBSeconds")
net_prev = get(prev, "networkEgressMB")
vol_prev = get(prev, "volumeGBSeconds")


# =========================
# DELTAS (HOURLY / DAILY)
# =========================
delta_cpu = max(cpu_now - cpu_prev, 0)
delta_mem_mb = max(mem_now - mem_prev, 0)
delta_net_mb = max(net_now - net_prev, 0)
delta_vol_gb_sec = max(vol_now - vol_prev, 0)

delta_mem_gb = delta_mem_mb / 1024
delta_net_gb = delta_net_mb / 1024


# =========================
# COST CALCULATION
# =========================
cpu_cost = delta_cpu * CPU_PRICE_PER_SEC
mem_cost = delta_mem_gb * MEMORY_PRICE_PER_GB_SEC
vol_cost = delta_vol_gb_sec * VOLUME_PRICE_PER_GB_SEC
net_cost = delta_net_gb * NETWORK_PRICE_PER_GB

total_cost = cpu_cost + mem_cost + vol_cost + net_cost


# =========================
# DISCORD EMBED
# =========================
timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

embed = {
    "title": "📊 Railway Usage & Estimated Cost",
    "color": 0x1abc9c,
    "fields": [
        {"name": "💻 CPU", "value": f"{delta_cpu:.0f} sec\n`${cpu_cost:.4f}`", "inline": True},
        {"name": "🧠 Memory", "value": f"{delta_mem_mb:.0f} MB-sec\n`${mem_cost:.4f}`", "inline": True},
        {"name": "📦 Volumes", "value": f"{delta_vol_gb_sec:.2f} GB-sec\n`${vol_cost:.4f}`", "inline": True},
        {"name": "🌐 Network", "value": f"{delta_net_gb:.3f} GB\n`${net_cost:.4f}`", "inline": True},
        {
            "name": "💰 Total Estimated Cost",
            "value": f"**`${total_cost:.4f}`**",
            "inline": False
        }
    ],
    "footer": {"text": f"Last update: {timestamp}"}
}


# =========================
# SEND OR EDIT MESSAGE
# =========================
try:
    if state["message_id"]:
        url = f"{DISCORD_WEBHOOK}/messages/{state['message_id']}"
        r = requests.patch(url, json={"embeds": [embed]})
        if r.status_code == 404:
            raise Exception("Message missing")
    else:
        r = requests.post(DISCORD_WEBHOOK, json={"embeds": [embed]})
        r.raise_for_status()
        state["message_id"] = r.json()["id"]

except Exception:
    r = requests.post(DISCORD_WEBHOOK, json={"embeds": [embed]})
    r.raise_for_status()
    state["message_id"] = r.json()["id"]


# =========================
# SAVE STATE
# =========================
safe_write_json(PREV_FILE, {
    "cpuSeconds": cpu_now,
    "memoryMBSeconds": mem_now,
    "networkEgressMB": net_now,
    "volumeGBSeconds": vol_now
})

safe_write_json(STATE_FILE, state)

print("✅ Usage report updated successfully")
