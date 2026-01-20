import requests
import os

RAILWAY_TOKEN = os.environ["RAILWAY_TOKEN"]
PROJECT_ID = os.environ["PROJECT_ID"]
DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]

query = """
query ProjectUsage($projectId: String!) {
  project(id: $projectId) {
    usage {
      cpuSeconds
      memoryMBSeconds
      networkEgressMB
    }
  }
}
"""

headers = {
    "Authorization": f"Bearer {RAILWAY_TOKEN}",
    "Content-Type": "application/json",
}

res = requests.post(
    "https://backboard.railway.app/graphql/v2",
    json={"query": query, "variables": {"projectId": PROJECT_ID}},
    headers=headers,
)

res.raise_for_status()

usage = res.json()["data"]["project"]["usage"]

message = (
    f"📊 **Railway Usage Update**\n"
    f"CPU: {usage['cpuSeconds'] / 3600:.2f} hours\n"
    f"Memory: {usage['memoryMBSeconds'] / 3600:.2f} MB-hours\n"
    f"Network: {usage['networkEgressMB']:.2f} MB"
)

requests.post(DISCORD_WEBHOOK, json={"content": message})
