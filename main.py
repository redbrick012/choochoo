import os
import json
import requests
from datetime import datetime, timezone

# ---------------------------
# Config
# ---------------------------
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")
USAGE_FILE = os.environ.get("USAGE_FILE", "usage.json")
PREV_FILE = os.environ.get("PREV_FILE", "usage_prev.json")

# Pricing rates
CPU_PRICE_PER_SEC = 0.00000772
MEMORY_PRICE_PER_GB_SEC = 0.00000386
VOLUME_PRICE_PER_GB_SEC = 0.00000006
NETWORK_PRICE_PER_GB = 0.05

# ---------------------------
# Load current usage JSON
# ---------------------------
try:
    with open(USAGE_FILE, "r") as f:
        usage = json.load(f)
except FileNotFoundError:
    print(f"Error: Usage file '{USAGE_FILE}' not found.")
    exit(1)

# ---------------------------
# Load previous usage snapshot
# ---------------------------
def empty_usage():
    return {
        "cpuSeconds": 0,
        "memoryMBSeconds": 0,
        "networkEgressMB": 0,
        "volumeGBSeconds": 0
    }

try:
    with open(PREV_FILE, "r") as f:
        prev_usage = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    prev_usage = empty_usage()

# ---------------------------
# Calculate deltas (daily usage)
# ---------------------------
delta_cpu = usage.get("cpuSeconds", 0) - prev_usage.get("cpuSeconds", 0)
delta_memory_mb = usage.get("memoryMBSeconds", 0) - prev_usage.get("memoryMBSeconds", 0)
delta_network_mb = usage.get("networkEgressMB", 0) - prev_usage.get("networkEgressMB", 0)
delta_volume_gb = usage.get("volumeGBSeconds", 0) - prev_usage.get("volumeGBSeconds", 0)

# Convert units
delta_memory_gb = delta_memory_mb / 1024
delta_network_gb = delta_network_mb / 1024

# ---------------------------
# Calculate estimated cost
# ---------------------------
cpu_cost = delta_cpu * CPU_PRICE_PER_SEC
memory_cost = delta_memory_gb * MEMORY_PRICE_PER_GB_SEC
volume_cost = delta_volume_gb * VOLUME_PRICE_PER_GB_SEC
network_cost = delta_network_gb * NETWORK_PRICE_PER_GB

total_cost = cpu_cost + memory_cost + volume_cost + network_cost

# ---------------------------
# Timestamp
# ---------------------------
timestamp = datetime.now(timezone.utc).isoformat()

# ---------------------------
# Build Discord Embed
# ---------------------------
embed = {
    "title": "📊 Railway Daily Usage & Estimated Cost",
    "color": 0x1abc9c,
    "fields": [
        {"name": "💻 CPU", "value": f"{delta_cpu} sec → ${cpu_cost:.4f}", "inline": True},
        {"name": "🧠 Memory", "value": f"{delta_memory_mb} MB-sec → ${memory_cost:.4f}", "inline": True},
        {"name": "📦 Volumes", "value": f"{delta_volume_gb} GB-sec → ${volume_cost:.4f}", "inline": True},
        {"name": "🌐 Network", "value": f"{delta_network_gb:.2f} GB → ${network_cost:.4f}", "inline": True},
        {"name": "💰 Total Estimated Cost", "value": f"${total_cost:.4f}", "inline": False}
    ],
    "footer": {"text": f"Snapshot taken at {timestamp} UTC"}
}

# ---------------------------
# Send to Discord
# ---------------------------
try:
    res = requests.post(DISCORD_WEBHOOK, json={"embeds": [embed]})
    res.raise_for_status()
    print("Embed sent to Discord successfully!")
except requests.exceptions.RequestException as e:
    print("Failed to send Discord embed:", e)
    exit(1)

# ---------------------------
# Update previous snapshot
# ---------------------------
with open(PREV_FILE, "w") as f:
    json.dump(usage, f)
