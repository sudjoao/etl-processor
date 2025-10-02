#!/usr/bin/env python3

import requests
import json

# Test CSV data (same as in the movies_10.csv file)
csv_data = {
    "headers": ["title", "genre", "rating", "year", "director", "actors", "budget", "box_office", "duration", "country", "language", "imdb_score"],
    "rows": [
        ["The Quiet Dawn", "Drama", "PG-13", "2019", "Sofia Coppola", "Emma Stone,Timothy Chalamet", "5000000", "12000000", "102", "USA", "English", "7.2"],
        ["Midnight Chase", "Action", "R", "2018", "Christopher Nolan", "Tom Hardy,Idris Elba,Emily Blunt", "85000000", "210000000", "130", "UK", "English", "7.8"],
        ["Love in Lisbon", "Romance", "PG", "2017", "Paula Ortiz", "Penélope Cruz,Andrés Velencoso", "10000000", "17000000", "95", "Portugal", "Portuguese", "6.9"]
    ]
}

# First, generate SQL from CSV data
print("🔄 Step 1: Generating SQL from CSV data...")
transform_payload = {
    "csvContent": "title,genre,rating,year,director,actors,budget,box_office,duration,country,language,imdb_score\nThe Quiet Dawn,Drama,PG-13,2019,Sofia Coppola,\"Emma Stone,Timothy Chalamet\",5000000,12000000,102,USA,English,7.2\nMidnight Chase,Action,R,2018,Christopher Nolan,\"Tom Hardy,Idris Elba,Emily Blunt\",85000000,210000000,130,UK,English,7.8\nLove in Lisbon,Romance,PG,2017,Paula Ortiz,\"Penélope Cruz,Andrés Velencoso\",10000000,17000000,95,Portugal,Portuguese,6.9",
    "fields": [
        {"name": "title", "selected": True, "format": "text", "order": 0},
        {"name": "genre", "selected": True, "format": "text", "order": 1},
        {"name": "rating", "selected": True, "format": "text", "order": 2},
        {"name": "year", "selected": True, "format": "number", "order": 3},
        {"name": "director", "selected": True, "format": "text", "order": 4},
        {"name": "actors", "selected": True, "format": "text", "order": 5},
        {"name": "budget", "selected": True, "format": "currency", "order": 6},
        {"name": "box_office", "selected": True, "format": "currency", "order": 7},
        {"name": "duration", "selected": True, "format": "number", "order": 8},
        {"name": "country", "selected": True, "format": "text", "order": 9},
        {"name": "language", "selected": True, "format": "text", "order": 10},
        {"name": "imdb_score", "selected": True, "format": "number", "order": 11}
    ],
    "tableName": "movies",
    "delimiter": ",",
    "includeCreateTable": True
}

response = requests.post('http://localhost:5001/api/transform', json=transform_payload)
if response.status_code != 200:
    print(f"❌ Failed to generate SQL: {response.status_code}")
    print(response.text)
    exit(1)

sql_result = response.json()
sql_content = sql_result['sql']
print(f"✅ SQL generated successfully ({len(sql_content)} characters)")

# Now test DW model generation with CSV data
print("\n🔄 Step 2: Generating DW model with CSV data...")
print(f"📊 CSV data being sent: {csv_data}")
dw_payload = {
    "sql": sql_content,
    "model_name": "TestDataWarehouse",
    "include_indexes": True,
    "include_partitioning": False,
    "csv_data": csv_data
}
print(f"📦 Payload keys: {list(dw_payload.keys())}")
print(f"📦 CSV data in payload: {dw_payload['csv_data'] is not None}")

response = requests.post('http://localhost:5001/api/generate-dw-model', json=dw_payload)
print(f"Status Code: {response.status_code}")

if response.status_code == 200:
    result = response.json()
    print("✅ DW Model generation successful!")
    
    # Check if we have DML statements
    if 'complete_schema' in result and 'dml_statements' in result['complete_schema']:
        dml_statements = result['complete_schema']['dml_statements']
        print(f"📊 DML statements found: {list(dml_statements.keys())}")
        
        # Check for real data in dimension tables
        for table_name, dml in dml_statements.items():
            if 'dim_' in table_name and dml:
                print(f"\n🔍 Checking {table_name}:")
                lines = dml.split('\n')[:5]  # First 5 lines
                for line in lines:
                    if 'INSERT INTO' in line and 'VALUES' in line:
                        print(f"  {line[:100]}...")
                        # Check if it contains real data (not placeholder)
                        if any(real_value in line for real_value in ['Drama', 'Action', 'Romance', 'Sofia Coppola', 'Christopher Nolan']):
                            print("  ✅ Contains real data!")
                        else:
                            print("  ❌ Contains placeholder data")
                        break
    else:
        print("❌ No DML statements found")

    # Save the complete SQL to a file for testing provisioning
    if 'complete_schema' in result:
        complete_sql = result['complete_schema'].get('complete_sql', '')
        if complete_sql:
            with open('data/test_generated_dw.sql', 'w') as f:
                f.write(complete_sql)
            print(f"\n💾 Complete SQL saved to data/test_generated_dw.sql ({len(complete_sql)} characters)")

            # Test provisioning
            print("\n🔄 Step 3: Testing provisioning with generated SQL...")
            session_response = requests.post('http://localhost:5001/api/nlq/session/create',
                                           json={"metadata": {"test": "csv-data-extraction"}})
            if session_response.status_code == 200:
                session_data = session_response.json()
                session_id = session_data['session_id']
                print(f"✅ Session created: {session_id}")

                # Provision the generated SQL
                provision_response = requests.post(f'http://localhost:5001/api/nlq/session/{session_id}/provision',
                                                 json={"sql": complete_sql})
                print(f"Provision Status Code: {provision_response.status_code}")
                if provision_response.status_code == 200:
                    print("✅ Provisioning successful!")
                else:
                    print(f"❌ Provisioning failed: {provision_response.text}")
            else:
                print(f"❌ Session creation failed: {session_response.status_code}")

else:
    print(f"❌ DW Model generation failed: {response.status_code}")
    print(f"Response: {response.text}")
