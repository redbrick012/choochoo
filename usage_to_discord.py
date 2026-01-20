import os
import subprocess
import json
import requests

# Environment variables
RAILWAY_TOKEN = os.environ["RAILWAY_TOKEN"]  # Railway API token
PROJECT_ID = os.environ["PROJECT_ID"]        # Railway project ID
DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]

# Step 1: Install Railway CLI if not already present
# (Optional: only needed if your container doesn't already have it)
# subprocess.run(["curl", "-fsSL", "https://raw.githubusercontent.com/railwayapp/cli/master/install.sh", "|", "sh"], check=True)

# Step 2: Fetch project usage via CLI
try:
    result = subprocess.run(
        ["railway", "usage", "--project", PROJECT_ID, "--json"],
        capture_output=True,
        text=True,
        check=True
    )
    usage = json.loads(result.stdout)
except subprocess.CalledProcessError as e:
    print("Error fetching usage:", e.stderr)
    exit(1)

# Step 3: Format message for Discord
cpu_hours = usage.get("cpuSeconds", 0) / 3600
memory_hours = usage.get("memoryMBSeconds", 0) / 3600
network_mb = usage.get("networkEgressMB", 0)

message = (
    f"📊 **Railway Usage Update**\n"
    f"CPU: {cpu_hours:.2f} hours\n"
    f"Memory: {memory_hours:.2f} MB-hours\n"
    f"Network: {network_mb:.2f} MB"
)

# Step 4: Post to Discord webhook
try:
    res = requests.post(DISCORD_WEBHOOK, json={"content": message})
    res.raise_for_status()
except requests.exceptions.RequestException as e:
    print("Failed to send Discord message:", e)
