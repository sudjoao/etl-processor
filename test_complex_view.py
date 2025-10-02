#!/usr/bin/env python3

import requests
import json

# Create a session first
response = requests.post('http://localhost:5001/api/nlq/session/create', 
                        json={"metadata": {"test": "complex-view"}})
session_data = response.json()
session_id = session_data['session']['session_id']
print(f"Created session: {session_id}")

# Test with a structure that mimics the DataWarehouse issue
complex_sql = """
CREATE TABLE dim_Genre (Genre_sk SERIAL PRIMARY KEY, genre VARCHAR(50));
CREATE TABLE dim_Content_Rating (Content_Rating_sk SERIAL PRIMARY KEY, rating VARCHAR(10));
CREATE TABLE fact_dados_importados (Genre_sk INT, Content_Rating_sk INT);

INSERT INTO dim_Genre (genre) VALUES ('Action');
INSERT INTO dim_Content_Rating (rating) VALUES ('PG');
INSERT INTO fact_dados_importados (Genre_sk, Content_Rating_sk) VALUES (1, 1);

CREATE VIEW vw_test AS
SELECT 
    Genre.genre, Content_Rating.rating
FROM fact_dados_importados f
LEFT JOIN dim_Genre Genre ON f.Genre_sk = Genre.Genre_sk
LEFT JOIN dim_Content_Rating Content_Rating ON f.Content_Rating_sk = Content_Rating.Content_Rating_sk;
"""

# Try to provision with the complex SQL
response = requests.post(f'http://localhost:5001/api/nlq/session/{session_id}/provision',
                        json={"sql": complex_sql})

print(f"Status Code: {response.status_code}")
print(f"Response: {response.json()}")
