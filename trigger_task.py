import requests
import json

url = "http://localhost:8000/api/tasks/execute"
payload = {
    "task_name": "Malaysia Solar PV"
}
headers = {
    "Content-Type": "application/json"
}

try:
    print(f"Triggering task: {payload['task_name']}...")
    response = requests.post(url, json=payload)
    response.raise_for_status()
    print("Task executed successfully!")
    print(json.dumps(response.json(), indent=2))
except requests.exceptions.RequestException as e:
    print(f"Error executing task: {e}")
    if hasattr(e, 'response') and e.response:
        print(f"Response: {e.response.text}")
