#!/usr/bin/env python3

import requests
import json

# Create a session first
response = requests.post('http://localhost:5001/api/nlq/session/create', 
                        json={"metadata": {"test": "simple-view"}})
session_data = response.json()
session_id = session_data['session']['session_id']
print(f"Created session: {session_id}")

# Test with a simple CREATE VIEW that mimics the problematic structure
simple_sql = """
CREATE TABLE test_table (id SERIAL PRIMARY KEY, name VARCHAR(50));
INSERT INTO test_table (name) VALUES ('test');

CREATE TABLE dim_genre (genre_sk SERIAL PRIMARY KEY, genre VARCHAR(50));
INSERT INTO dim_genre (genre) VALUES ('Action');

CREATE VIEW test_view AS
SELECT 
    g.genre
FROM test_table t
LEFT JOIN dim_genre g ON t.id = g.genre_sk;
"""

# Try to provision with the simple SQL
response = requests.post(f'http://localhost:5001/api/nlq/session/{session_id}/provision',
                        json={"sql": simple_sql})

print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
