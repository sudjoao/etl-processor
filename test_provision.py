#!/usr/bin/env python3
import requests
import json

# Read the SQL file
with open('data/DataWarehouse_complete-11.sql', 'r') as f:
    sql_content = f.read()

# Session ID from the previous request
session_id = "ef90a3e3-f2b0-4466-9708-100504f6e1d1"

# Prepare the request
url = f"http://localhost:5001/api/nlq/session/{session_id}/provision"
headers = {"Content-Type": "application/json"}
data = {"sql": sql_content}

# Send the request
try:
    response = requests.post(url, headers=headers, json=data)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
