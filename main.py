import os
import json
import requests
from datetime import datetime, timezone

# ---------------------------
# Config
# ---------------------------
DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")
USAGE_FILE = os.environ.get("USAGE_FILE", "usage.json")

# Pricing rates
CPU_PRICE_PER_SEC = 0.00000772
MEMORY_PRICE_PER_GB_SEC = 0.00000386
VOLUME_PRICE_PER_GB_SEC = 0.00000006
NETWORK_PRICE_PER_GB = 0.05

# ---------------------------
# Load usage JSON
# ---------------------------
try:
    with open(USAGE_FILE, "r") as f:
        usage = json.load(f)
except FileNotFoundError:
    print(f"Error: Usage file '{USAGE_FILE}' not found.")
    exit(1)
except json.JSONDecodeError:
    print(f"Error: Usage file '{USAGE_FILE}' is not valid JSON.")
    exit(1)

# ---------------------------
# Extract usage values
# ---------------------------
cpu_seconds = usage.get("cpuSeconds", 0)
memory_mb_seconds = usage.get("memoryMBSeconds", 0)
network_mb = usage.get("networkEgressMB", 0)
volume_gb_seconds = usage.get("volumeGBSeconds", 0)

memory_gb_seconds = memory_mb_seconds / 1024
network_gb = network_mb / 1024

# ---------------------------
# Calculate costs
# ---------------------------
cpu_cost = cpu_seconds * CPU_PRICE_PER_SEC
memory_cost = memory_gb_seconds * MEMORY_PRICE_PER_GB_SEC
volume_cost = volume_gb_seconds * VOLUME_PRICE_PER_GB_SEC
network_cost = network_gb * NETWORK_PRICE_PER_GB

estimated_cost = cpu_cost + memory_cost + volume_cost + network_cost

# ---------------------------
# Timestamp
# ---------------------------
timestamp = datetime.now(timezone.utc).isoformat()

# ---------------------------
# Build Discord Embed
# ---------------------------
embed = {
    "title": "📊 Railway Usage & Estimated Cost",
    "color": 0x1abc9c,
    "fields": [
        {"name": "💻 CPU", "value": f"{cpu_seconds} sec → ${cpu_cost:.4f}", "inline": True},
        {"name": "🧠 Memory", "value": f"{memory_mb_seconds} MB-sec → ${memory_cost:.4f}", "inline": True},
        {"name": "📦 Volumes", "value": f"{volume_gb_seconds} GB-sec → ${volume_cost:.4f}", "inline": True},
        {"name": "🌐 Network", "value": f"{network_gb:.2f} GB → ${network_cost:.4f}", "inline": True},
        {"name": "💰 Total Estimated Cost", "value": f"${estimated_cost:.4f}", "inline": False}
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
