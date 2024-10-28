import os
import requests
import json
from datetime import datetime

# GitHub repository name and access token from environment variables
repo_name = os.getenv('REPO_NAME')
token = os.getenv('TOKEN')

# Set up the headers with the token for authentication
headers = {
    'Authorization': f'token {token}',
    'Accept': 'application/vnd.github.v3+json'
}

# Define GitHub API URLs for traffic data (views and clones)
traffic_endpoints = {
    'views': f'https://api.github.com/repos/{repo_name}/traffic/views',
    'clones': f'https://api.github.com/repos/{repo_name}/traffic/clones'
}

# Ensure the 'insights' directory exists
os.makedirs('insights', exist_ok=True)
today = datetime.now().strftime('%Y-%m-%d')

# Fetch and process traffic data for views and clones
for insight_type, url in traffic_endpoints.items():
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        data = response.json()
        
        # Prepare the data to save, including totals and daily breakdown
        insight_data = {
            "total_count": data.get("count"),
            "total_uniques": data.get("uniques"),
            "daily_breakdown": [
                {
                    "date": entry["timestamp"],
                    "count": entry["count"],
                    "uniques": entry["uniques"]
                }
                for entry in data.get("views" if insight_type == "views" else "clones", [])
            ]
        }
        
        # Save the data to a single 'insights' directory with type and date in filename
        file_path = f'insights/{insight_type}_summary_{today}.json'
        with open(file_path, 'w') as f:
            json.dump(insight_data, f, indent=4)
        
        print(f"{insight_type.capitalize()} insights data saved to {file_path}")
    else:
        print(f"Failed to retrieve {insight_type} data: {response.status_code} - {response.text}")
