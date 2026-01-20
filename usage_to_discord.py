import requests
import os

RAILWAY_TOKEN = os.environ["RAILWAY_TOKEN"]
PROJECT_ID = os.environ["PROJECT_ID"]
DISCORD_WEBHOOK = os.environ["DISCORD_WEBHOOK"]

query = """
query ProjectUsage($projectId: String!) {
  project(id: $projectId) {
    metrics {
      cpuSeconds
      memorySeconds
      networkEgressBytes
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

# DEBUG — print the real response
print("STATUS:", res.status_code)
print("RESPONSE:", res.text)
exit(0)


res.raise_for_status()

metrics = res.json()["data"]["project"]["metrics"]

message = (
    f"📊 **Railway Usage Update**\n"
    f"CPU: {metrics['cpuSeconds'] / 3600:.2f} hours\n"
    f"Memory: {metrics['memorySeconds'] / 3600:.2f} MB-hours\n"
    f"Network: {metrics['networkEgressBytes'] / (1024*1024):.2f} MB"
)

requests.post(DISCORD_WEBHOOK, json={"content": message})
