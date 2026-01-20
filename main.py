import os
import json
import requests

DISCORD_WEBHOOK = os.environ.get("DISCORD_WEBHOOK")
USAGE_FILE = os.environ.get("USAGE_FILE", "usage.json")

try:
    with open(USAGE_FILE, "r") as f:
        usage = json.load(f)
except FileNotFoundError:
    print(f"Error: Usage file '{USAGE_FILE}' not found.")
    exit(1)
except json.JSONDecodeError:
    print(f"Error: Usage file '{USAGE_FILE}' is not valid JSON.")
    exit(1)

cpu_hours = usage.get("cpuSeconds", 0) / 3600
memory_hours = usage.get("memoryMBSeconds", 0) / 3600
network_mb = usage.get("networkEgressMB", 0)

message = (
    f"📊 **Railway Usage Update**\n"
    f"CPU: {cpu_hours:.2f} hours\n"
    f"Memory: {memory_hours:.2f} MB-hours\n"
    f"Network: {network_mb:.2f} MB"
)

try:
    res = requests.post(DISCORD_WEBHOOK, json={"content": message})
    res.raise_for_status()
    print("Mess
