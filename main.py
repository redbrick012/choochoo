import os
import json
import requests
from datetime import datetime, timezone

# ---------------------------
# CONFIG
# ---------------------------
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")
PREV_FILE = os.environ.get("PREV_FILE", "prev_usage.json")

# Safety check
if not DISCORD_WEBHOOK:
    print("Error: DISCORD_WEBHOOK environment variable not set!")
    exit(1)

# Resource allocation (replace with your project’s actual values)
CPU_VCPUS = float(os.environ.get("CPU_VCPUS", 0.5))      # e.g., 0.5 vCPU
MEMORY_GB = float(os.environ.get("MEMORY_GB", 0.128))    # e.g., 128 MB = 0.128 GB
VOLUME_GB = float(os.environ.get("VOLUME_GB", 1))        # persistent volume size
NETWORK_GB = float(os.environ.get("NETWORK_GB", 0))      # egress since last run

# Pricing (from Railway)
CPU_PRICE_PER_SEC = 0.00000772
MEMORY_PRICE_PER_GB_SEC = 0.00000386
VOLUME_PRICE_PER_GB_SEC = 0.00000006
NETWORK_PRICE_PER_GB = 0.05

# ---------------------------
# Load previous usage snapshot
# ---------------------------
if os.path.exists(PREV_FILE):
    with open(PREV_FILE, "r") as f:
        prev = json.load(f)
        last_run = datetime.fromisoformat(prev.get("timestamp"))
        prev_network_gb = prev.get("network_gb", 0)
else:
    # First run
    last_run = None
    prev_network_gb = 0

# ---------------------------
# Compute time delta
# ---------------------------
now = datetime.now(timezone.utc)
if last_run:
    delta_seconds = (now - last_run).total_seconds()
else:
    # first run, assume 1 hour
    delta_seconds = 3600

# ---------------------------
# Compute network delta
# ---------------------------
delta_network_gb = max(0, NETWORK_GB - prev_network_gb)

# ---------------------------
# Compute cost
# ---------------------------
cpu_cost = CPU_VCPUS * delta_seconds * CPU_PRICE_PER_SEC
memory_cost = MEMORY_GB * delta_seconds * MEMORY_PRICE_PER_GB_SEC
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
        {"name": "💻 CPU", "value": f"{CPU_VCPUS} vCPU × {int(delta_seconds)} sec → ${cpu_cost:.4f}", "inline": True},
        {"name": "🧠 Memory", "value": f"{MEMORY_GB} GB × {int(delta_seconds)} sec → ${memory_cost:.4f}", "inline": True},
        {"name": "📦 Volumes", "value": f"{VOLUME_GB} GB × {int(delta_seconds)} sec → ${volume_cost:.4f}", "inline": True},
        {"name": "🌐 Network", "value": f"{delta_network_gb:.2f} GB → ${network_cost:.4f}", "inline": True},
        {"name": "💰 Total Estimated Cost", "value": f"${total_cost:.4f}", "inline": False}
    ],
    "footer": {"text": f"Snapshot taken at {now.isoformat()} UTC"}
}

# ---------------------------
# Send to Discord
# ---------------------------
try:
    res = requests.post(DISCORD_WEBHOOK, json={"embeds": [embed]})
    res.raise_for_status()
    print("✅ Embed sent to Discord successfully!")
except requests.exceptions.RequestException as e:
    print("❌ Failed to send Discord embed:", e)
    exit(1)

# ---------------------------
# Save snapshot
# ---------------------------
snapshot = {
    "timestamp": now.isoformat(),
    "network_gb": NETWORK_GB
}
with open(PREV_FILE, "w") as f:
    json.dump(snapshot, f)
