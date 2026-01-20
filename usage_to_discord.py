import requests
import os

RAILWAY_TOKEN = os.environ["RAILWAY_TOKEN"]
PROJECT_ID = os.environ["PROJECT_ID"]

query = """
query Test($projectId: ID!) {
  project(id: $projectId) {
    id
    name
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

print("STATUS:", res.status_code)
print("RESPONSE:", res.text)
exit(0)
