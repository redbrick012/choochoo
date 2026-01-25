import os
import json
import requests
from datetime import datetime, timezone
import random

# ===========================
# CONFIG
# ===========================
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")
STATE_FILE = "/app/data/usage_state.json"

if not DISCORD_WEBHOOK:
    raise RuntimeError("DISCORD_WEBHOOK env var not set")

# ===========================
# PRICING (Railway-like)
# ===========================
CPU_PRICE_PER_SEC = 0.00000772
MEM_PRICE_PER_GB_SEC = 0.00000386
VOLUME_PRICE_PER_GB_SEC = 0.00000006
NETWORK_PRICE_PER_GB = 0.05

# ===========================
# DEFAULT RESOURCES
# ===========================
CPU_BASE = float(os.environ.get("CPU_VCPUS", 0.5))
MEM_BASE = float(os.environ.get("MEMORY_GB", 0.128))
VOLUME_GB = float(os.environ.get("VOLUME_GB", 1.0))

# ===========================
# LOAD STATE
# ===========================
state = {}
if os.path.exists(STATE_FILE):
    with open(STATE_FILE, "r") as f:
        state = json.load(f)

last_run = (
    datetime.fromisoformat(state["last_run"])
    if "last_run" in state
    else None
)
message_id = state.get("message_id")
network_total = state.get("network_total_gb", 0.0)

# ===========================
# TIME DELTA
# ===========================
now = datetime.now(timezone.utc)
delta_seconds = int((now - last_run).total_seconds()) if last_run else 3600

# ===========================
# SIMULATED USAGE
# ===========================
cpu = max(0.1, CPU_BASE + random.uniform(-0.05, 0.05))
mem = max(0.05, MEM_BASE + random.uniform(-0.01, 0.01))
network_delta = random.uniform(0.005, 0.05)
network_total += network_delta

# ===========================
# COST CALC
# ===========================
cpu_cost = cpu * delta_seconds * CPU_PRICE_PER_SEC
mem_cost = mem * delta_seconds * MEM_PRICE_PER_GB_SEC
vol_cost = VOLUME_GB * delta_seconds * VOLUME_PRICE_PER_GB_SEC
net_cost = network_delta * NETWORK_PRICE_PER_GB
total_cost = cpu_cost + mem_cost + vol_cost + net_cost

# ===========================
# DISCORD EMBED
# ===========================
embed = {
    "title": "📊 Railway Usage & Estimated Cost",
    "color": 0x2ecc71,
    "fields": [
        {
            "name": "💻 CPU",
            "value": f"{cpu:.2f} vCPU × {delta_seconds}s\n`${cpu_cost:.5f}`",
            "inline": True,
        },
        {
            "name": "🧠 Memory",
            "value": f"{mem:.3f} GB × {delta_seconds}s\n`${mem_cost:.5f}`",
            "inline": True,
        },
        {
            "name": "📦 Volume",
            "value": f"{VOLUME_GB} GB × {delta_seconds}s\n`${vol_cost:.5f}`",
            "inline": True,
        },
        {
            "name": "🌐 Network",
            "value": f"{network_delta:.3f} GB\n`${net_cost:.5f}`",
            "inline": True,
        },
        {
            "name": "💰 Total (this period)",
            "value": f"**${total_cost:.5f}**",
            "inline": False,
        },
        {
            "name": "🫀 Heartbeat",
            "value": f"Run @ `{now.isoformat()}`",
            "inline": False,
        },
    ],
}

# ===========================
# SEND OR EDIT MESSAGE
# ===========================
if message_id:
    r = requests.patch(
        f"{DISCORD_WEBHOOK}/messages/{message_id}",
        json={"embeds": [embed]},
    )
    if r.status_code == 404:
        message_id = None

if not message_id:
    r = requests.post(DISCORD_WEBHOOK, json={"embeds": [embed]})
    r.raise_for_status()
    message_id = r.json()["id"]

# ===========================
# SAVE STATE
# ===========================
os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
with open(STATE_FILE, "w") as f:
    json.dump(
        {
            "last_run": now.isoformat(),
            "network_total_gb": network_total,
            "message_id": message_id,
        },
        f,
        indent=2,
    )

print("✅ Usage report updated at", now.isoformat())
