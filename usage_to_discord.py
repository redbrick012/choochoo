import os
import subprocess
import json
import requests

RAILWAY_TOKEN = os.environ["RAILWAY_TOKEN"]
PROJECT_ID = os.environ["PROJECT_ID"]
DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]

# Install Railway CLI
subprocess.run(
    ["curl", "-fsSL", "https://raw.githubusercontent.com/railwayapp/cli/master/install.sh", "|", "sh"],
    shell=True,
    check=True
)

# Fetch usage
result = subprocess.run(
    ["railway", "usage", "--project", PROJECT_ID, "--json"],
    capture_output=True,
    text=True,
    check=True
)
usage = json.loads(result.stdout)

message = (
    f"📊 **Railway Usage Update**\n"
    f"CPU: {usage['cpuSeconds'] / 3600:.2f} hours\n"
    f"Memory: {usage['memoryMBSeconds'] / 3600:.2f} MB-hours\n"
    f"Network: {usage['networkEgressMB']:.2f} MB"
)

requests.post(DISCORD_WEBHOOK, json={"content": message})
