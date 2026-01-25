import os
import json
import requests
from datetime import datetime, timezone
import random

# ---------------------------
# CONFIG
# ---------------------------
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")
PREV_FILE = "/app/data/prev_usage.json"
if not DISCORD_WEBHOOK:
    print("❌ DISCORD_WEBHOOK not set!")
    exit(1)

# ---------------------------
# Defaults / Simulated resources
# ---------------------------
CPU_BASE = float(os.environ.get("CPU_VCPUS", 0.5))
MEM_BASE = float(os.environ.get("MEMORY_GB", 0.128))
VOLUME_GB = float(os.environ.get("VOLUME_GB", 1))

# Pricing (Railway rates)
CPU_PRICE_PER_SEC = 0.00000772
MEM_PRICE_PER_GB_SEC = 0.00000386
VOLUME_PRICE_PER_GB_SEC = 0.00000006
NETWORK_PRICE_PER_GB = 0.05

# ---------------------------
# Load previous state
# ---------------------------
state = {}
if os.path.exists(PREV_FILE):
    with open(PREV_FILE, "r") as f:
        state = json.load(f)
last_run = datetime.fromisoformat(state.get("timestamp")) if state.get("timestamp") else None
prev_network_gb = state.get("network_gb", 0)
message_id = state.get("message_id")

# ---------------------------
# Compute deltas
# ---------------------------
now = datetime.now(timezone.utc)
delta_seconds = (now - last_run).total_seconds() if last_run else 3600

# ---------------------------
# Simulate current usage
# ---------------------------
CPU_VCPUS = max(0, CPU_BASE + random.uniform(-0.1, 0.1))
MEMORY_GB = max(0, MEM_BASE + random.uniform(-0.01, 0.01))
NETWORK_GB = prev_network_gb + random.uniform(0, 0.05)  # small random network growth

delta_network_gb = max(0, NETWORK_GB - prev_network_gb)

# ---------------------------
# Compute costs
# ---------------------------
cpu_cost = CPU_VCPUS * delta_seconds * CPU_PRICE_PER_SEC
memory_cost = MEMORY_GB * delta_seconds * MEM_PRICE_PER_GB_SEC
volume_cost = VOLUME_GB * delta_seconds * VOLUME_PRICE_PER_GB_SEC
network_cost = delta_network_gb * NETWORK_PRICE_PER_GB
total_cost = cpu_cost + memory_cost + volume_cost + network_cost

# ---------------------------
# Build Discord embed
# ---------------------------
embed = {
    "title": "📊 Railway Usage & Estimated Cost",
    "color": 0x1abc9c,
    "fields": [
        {"name": "💻 CPU", "value": f"{CPU_VCPUS:.2f} vCPU × {int(delta_seconds)} sec → ${cpu_cost:.4f}", "inline": True},
        {"name": "🧠 Memory", "value": f"{MEMORY_GB:.3f} GB × {int(delta_seconds)} sec → ${memory_cost:.4f}", "inline": True},
        {"name": "📦 Volumes", "value": f"{VOLUME_GB} GB × {int(delta_seconds)} sec → ${volume_cost:.4f}", "inline": True},
        {"name": "🌐 Network", "value": f"{delta_network_gb:.3f} GB → ${network_cost:.4f}", "inline": True},
        {"name": "💰 Total Estimated Cost", "value": f"${total_cost:.4f}", "inline": False}
    ],
    "footer": {"text": f"Snapshot at {now.isoformat()} UTC"}
}

# ---------------------------
# Send / Update Discord message
# ---------------------------
try:
    # If previous message ID exists, try to edit
    if message_id:
        res = requests.patch(
            f"{DISCORD_WEBHOOK}/messages/{message_id}",
            json={"embeds": [embed]}
        )
        if res.status_code == 404:
            # Message deleted → create new
            raise Exception("Previous message not found")
    else:
        raise Exception("No previous message ID")

except Exception:
    # Send new message
    res = requests.post(DISCORD_WEBHOOK, json={"embeds": [embed]})
    res.raise_for_status()
    message_id = res.json().get("id")

print(f"✅ Embed sent/updated at {now.isoformat()}")

# ---------------------------
# Save state
# ---------------------------
state = {
    "timestamp": now.isoformat(),
    "network_gb": NETWORK_GB,
    "message_id": message_id
}
with open(PREV_FILE, "w") as f:
    json.dump(state, f, indent=2)
